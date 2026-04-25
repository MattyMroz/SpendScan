"""Gemini API client for receipt analysis."""

from __future__ import annotations

import asyncio
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
    """Direct Google Gemini API client for receipt JSON extraction."""

    __slots__ = ("_client", "_settings", "_validator")

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        validator: ReceiptOutputValidator | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._validator = validator or ReceiptOutputValidator()
        self._client: Any | None = None

    @property
    def is_available(self) -> bool:
        """Return whether Gemini API key and SDK are available."""
        return bool(self._settings.gemini_api_key_value)

    async def analyze_receipt(self, *, ocr_text: str, image_path: Path | None = None) -> ReceiptAnalysisResult:
        """Analyze OCR text and optional image through Gemini."""
        if not self._settings.gemini_api_key_value:
            msg = "SPENDSCAN_GEMINI_API_KEY is missing"
            raise ConfigurationError(msg)

        models = _unique_models(
            self._settings.gemini_model,
            self._settings.gemini_fallback_model,
            self._settings.gemini_gemma_fallback_model,
        )
        last_error: Exception | None = None
        for attempt in range(1, self._settings.gemini_retry_attempts + 1):
            for model_name in models:
                try:
                    raw_text = await self._call_api(model_name=model_name, ocr_text=ocr_text, image_path=image_path)
                    return self._validator.validate(raw_text, raw_ocr_text=ocr_text)
                except (ExternalServiceError, OutputValidationError) as exc:
                    last_error = exc
                    logger.warning("Gemini model {} failed on attempt {}: {}", model_name, attempt, exc)

            if attempt < self._settings.gemini_retry_attempts:
                await asyncio.sleep(self._settings.gemini_retry_delay_seconds)

        msg = "Gemini receipt analysis failed for all configured models"
        raise ExternalServiceError(msg) from last_error

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = genai.Client(api_key=self._settings.gemini_api_key_value)
        return self._client

    async def _call_api(self, *, model_name: str, ocr_text: str, image_path: Path | None) -> str:
        try:
            response = await asyncio.to_thread(
                self._generate_content,
                model_name,
                ocr_text,
                image_path,
            )
        except Exception as exc:
            msg = f"Gemini API call failed for {model_name}: {exc}"
            raise ExternalServiceError(msg) from exc

        text = getattr(response, "text", "")
        if not isinstance(text, str) or not text.strip():
            msg = f"Gemini API returned an empty response for {model_name}"
            raise ExternalServiceError(msg)
        return text

    def _generate_content(self, model_name: str, ocr_text: str, image_path: Path | None) -> Any:
        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=self._settings.gemini_temperature,
            max_output_tokens=self._settings.gemini_max_output_tokens,
            response_mime_type="application/json",
        )
        contents: list[Any] = [build_receipt_prompt(ocr_text)]
        if image_path is not None and image_path.exists():
            contents.append(types.Part.from_bytes(data=image_path.read_bytes(), mime_type=_mime_type(image_path)))
        return client.models.generate_content(model=model_name, contents=contents, config=config)


def _unique_models(primary: str, fallback: str, gemma_fallback: str) -> tuple[str, ...]:
    models = [
        primary or DEFAULT_GEMINI_MODEL,
        fallback or DEFAULT_GEMINI_FALLBACK_MODEL,
        gemma_fallback or DEFAULT_GEMINI_GEMMA_FALLBACK_MODEL,
    ]
    return tuple(dict.fromkeys(model for model in models if model))


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"
