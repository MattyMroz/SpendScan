from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import pytest

from spendscan.config import Settings
from spendscan.errors import ExternalServiceError
from spendscan.llm.gemini import (
    GeminiReceiptClient,
    _thinking_config,
    _thinking_config_for_model,
    _unique_models,
)


def test_unique_models_uses_gemma_as_last_fallback() -> None:
    models = _unique_models("gemini-3.1-flash-lite-preview", "gemini-flash-lite-latest", "gemma-4-31b-it")

    assert models == ("gemini-3.1-flash-lite-preview", "gemini-flash-lite-latest", "gemma-4-31b-it")


def test_unique_models_deduplicates_repeated_models() -> None:
    models = _unique_models("gemini-flash-lite-latest", "gemini-flash-lite-latest", "gemma-4-31b-it")

    assert models == ("gemini-flash-lite-latest", "gemma-4-31b-it")


def test_thinking_config_can_disable_thinking_budget() -> None:
    config = _thinking_config(0)

    assert config is not None
    assert config.thinking_budget == 0


def test_thinking_config_can_be_omitted() -> None:
    assert _thinking_config(None) is None


def test_thinking_config_for_gemma_is_always_none() -> None:
    assert _thinking_config_for_model("gemma-4-31b-it", 0) is None
    assert _thinking_config_for_model("gemma-4-31b-it", 256) is None


def test_thinking_config_for_gemini_respects_budget() -> None:
    config = _thinking_config_for_model("gemini-3.1-flash-lite-preview", 0)

    assert config is not None
    assert config.thinking_budget == 0


class _SlowGeminiClient(GeminiReceiptClient):
    def _generate_content(self, api_key: str, model_name: str, ocr_text: str, image_paths: tuple[Path, ...]) -> Any:
        time.sleep(self._settings.gemini_timeout_seconds + 5.0)
        return object()

    def _get_client(self) -> Any:
        return self


def test_call_api_raises_external_service_error_on_timeout() -> None:
    settings = Settings(
        gemini_api_key="dummy-key",  # type: ignore[arg-type]
        gemini_timeout_seconds=0.05,
        gemini_retry_attempts=1,
    )
    client = _SlowGeminiClient(settings=settings)

    with pytest.raises(ExternalServiceError, match="timeout"):
        asyncio.run(
            client._call_api(
                api_key="dummy-key", model_name="gemini-3.1-flash-lite-preview", ocr_text="x", image_paths=()
            )
        )
