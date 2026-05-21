from __future__ import annotations

from spendscan.llm.gemini import _thinking_config, _unique_models


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
