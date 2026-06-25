"""Gemini API client for receipt analysis.

Provides GeminiReceiptClient, which calls the Google Gemini API to extract
structured JSON from receipt images and OCR text. Supports primary and backup
API keys, multiple fallback models, and configurable retry logic.

Typical usage:

    client = GeminiReceiptClient()
    result = await client.analyze_receipt(ocr_text="...", image_path=Path("receipt.jpg"))
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from loguru import logger

from spendscan.config import (
    DEFAULT_GEMINI_FALLBACK_MODEL,
    DEFAULT_GEMINI_GEMMA_FALLBACK_MODEL,
    DEFAULT_GEMINI_MODEL,
    Settings,
    get_settings,
)
from spendscan.errors import ConfigurationError, ExternalServiceError, OutputValidationError

from .prompt import SYSTEM_PROMPT, build_receipt_prompt
from .schemas import ReceiptAnalysisResult
from .validation import ReceiptOutputValidator


class GeminiReceiptClient:
    """Direct Google Gemini API client for receipt JSON extraction.

    Wraps the Google GenAI SDK to send receipt images and OCR text to
    Gemini and return a validated ReceiptAnalysisResult. Rotates through
    configured API keys and fallback models on transient failures.

    Attributes:
        is_available: Whether a Gemini API key is configured.
    """

    __slots__ = ("_clients", "_settings", "_validator")

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        validator: ReceiptOutputValidator | None = None,
    ) -> None:
        """Initialize the client with optional settings and validator.

        Args:
            settings: Application settings. Uses global settings if None.
            validator: Output validator. Creates a default one if None.
        """
        self._settings = settings or get_settings()
        self._validator = validator or ReceiptOutputValidator()
        self._clients: dict[str, Any] = {}

    @property
    def is_available(self) -> bool:
        """Return whether Gemini API key and SDK are available."""
        return bool(self._settings.gemini_api_key_value)

    async def analyze_receipt(
        self,
        *,
        ocr_text: str,
        image_path: Path | None = None,
        image_paths: Sequence[Path] | None = None,
    ) -> ReceiptAnalysisResult:
        """Analyze OCR text and optional receipt image(s) through Gemini.

        Iterates over all configured API keys and fallback models for each
        retry attempt. Returns the first successful validated result.

        Args:
            ocr_text: Raw OCR transcript of the receipt.
            image_path: Single receipt image path (mutually exclusive with
                image_paths; ignored when image_paths is provided).
            image_paths: Ordered sequence of receipt image paths (for
                multi-page receipts). Non-existent paths are silently skipped.

        Returns:
            Validated receipt analysis result.

        Raises:
            ConfigurationError: If no Gemini API key is configured.
            ExternalServiceError: If all keys, models, and retries are
                exhausted without a successful response.
        """
        api_keys = _unique_api_keys(
            self._settings.gemini_api_key_value,
            self._settings.gemini_api_key_backup_value,
        )
        if not api_keys:
            msg = "SPENDSCAN_GEMINI_API_KEY is missing"
            raise ConfigurationError(msg)

        resolved_image_paths = _resolved_image_paths(image_path=image_path, image_paths=image_paths)
        models = _unique_models(
            self._settings.gemini_model,
            self._settings.gemini_fallback_model,
            self._settings.gemini_gemma_fallback_model,
        )
        last_error: Exception | None = None
        for attempt in range(1, self._settings.gemini_retry_attempts + 1):
            for api_key in api_keys:
                key_label = _key_label(api_key, api_keys)
                for model_name in models:
                    try:
                        raw_text = await self._call_api(
                            api_key=api_key,
                            model_name=model_name,
                            ocr_text=ocr_text,
                            image_paths=resolved_image_paths,
                        )
                        return self._validator.validate(raw_text, raw_ocr_text=ocr_text)
                    except (ExternalServiceError, OutputValidationError) as exc:
                        last_error = exc
                        logger.warning(
                            "Gemini key={} model={} attempt={} failed: {}", key_label, model_name, attempt, exc
                        )

            if attempt < self._settings.gemini_retry_attempts:
                await asyncio.sleep(self._settings.gemini_retry_delay_seconds)

        msg = "Gemini receipt analysis failed for all configured models"
        raise ExternalServiceError(msg) from last_error

    def _get_client(self, api_key: str) -> Any:
        """Return a cached genai.Client for api_key, creating one if absent."""
        client = self._clients.get(api_key)
        if client is None:
            client = genai.Client(api_key=api_key)
            self._clients[api_key] = client
        return client

    async def _call_api(self, *, api_key: str, model_name: str, ocr_text: str, image_paths: tuple[Path, ...]) -> str:
        """Send a single API request and return the raw response text.

        Runs the blocking SDK call in a thread pool and enforces the
        configured timeout. Wraps all SDK errors in ExternalServiceError.

        Raises:
            ExternalServiceError: On timeout, SDK error, or empty response.
        """
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_content,
                    api_key,
                    model_name,
                    ocr_text,
                    image_paths,
                ),
                timeout=self._settings.gemini_timeout_seconds,
            )
        except TimeoutError as exc:
            msg = f"Gemini API call for {model_name} exceeded {self._settings.gemini_timeout_seconds:.0f}s timeout"
            raise ExternalServiceError(msg) from exc
        except Exception as exc:
            msg = f"Gemini API call failed for {model_name}: {exc}"
            raise ExternalServiceError(msg) from exc

        text = getattr(response, "text", "")
        if not isinstance(text, str) or not text.strip():
            msg = f"Gemini API returned an empty response for {model_name}"
            raise ExternalServiceError(msg)
        return text

    def _generate_content(self, api_key: str, model_name: str, ocr_text: str, image_paths: tuple[Path, ...]) -> Any:
        """Call the Gemini generate_content endpoint synchronously.

        Builds the full contents list (text prompt + image parts) and
        attaches the generation config before dispatching to the SDK.
        Intended to be called from a thread pool via asyncio.to_thread.
        """
        client = self._get_client(api_key)
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=self._settings.gemini_temperature,
            max_output_tokens=self._settings.gemini_max_output_tokens,
            response_mime_type="application/json",
            thinking_config=_thinking_config_for_model(model_name, self._settings.gemini_thinking_budget),
        )
        contents: list[Any] = [build_receipt_prompt(ocr_text)]
        contents.extend(
            types.Part.from_bytes(data=image_path.read_bytes(), mime_type=_mime_type(image_path))
            for image_path in image_paths
        )
        return client.models.generate_content(model=model_name, contents=contents, config=config)


def _unique_api_keys(*keys: str) -> tuple[str, ...]:
    """Return non-empty, deduplicated API keys preserving insertion order."""
    return tuple(dict.fromkeys(key for key in keys if key))


def _key_label(api_key: str, all_keys: tuple[str, ...]) -> str:
    """Return a human-readable label ("primary" or "backup") for log output."""
    if len(all_keys) <= 1:
        return "primary"
    return "primary" if api_key == all_keys[0] else "backup"


def _unique_models(primary: str, fallback: str, gemma_fallback: str) -> tuple[str, ...]:
    """Return the ordered, deduplicated list of models to try, filling defaults."""
    models = [
        primary or DEFAULT_GEMINI_MODEL,
        fallback or DEFAULT_GEMINI_FALLBACK_MODEL,
        gemma_fallback or DEFAULT_GEMINI_GEMMA_FALLBACK_MODEL,
    ]
    return tuple(dict.fromkeys(model for model in models if model))


def _thinking_config(thinking_budget: int | None) -> types.ThinkingConfig | None:
    """Return a ThinkingConfig for the given budget, or None to disable thinking."""
    if thinking_budget is None:
        return None
    return types.ThinkingConfig(thinking_budget=thinking_budget)


def _thinking_config_for_model(model_name: str, thinking_budget: int | None) -> types.ThinkingConfig | None:
    """Return the appropriate ThinkingConfig, suppressing it for Gemma models.

    Gemma family rejects ThinkingConfig with HTTP 400 INVALID_ARGUMENT,
    so thinking must be disabled unconditionally for those models.
    """
    # Gemma family rejects ThinkingConfig with HTTP 400 INVALID_ARGUMENT.
    if model_name.startswith("gemma"):
        return None
    return _thinking_config(thinking_budget)


def _resolved_image_paths(*, image_path: Path | None, image_paths: Sequence[Path] | None) -> tuple[Path, ...]:
    """Resolve caller-supplied image arguments to a tuple of existing paths.

    image_paths takes precedence over image_path when both are provided.
    Paths that do not exist on disk are silently dropped.
    """
    if image_paths is not None:
        return tuple(path for path in image_paths if path.exists())
    if image_path is not None and image_path.exists():
        return (image_path,)
    return ()


def _mime_type(path: Path) -> str:
    """Return the MIME type string for an image path based on its extension."""
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"
