"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_GEMINI_MODEL: Final[str] = "gemini-3.1-flash-lite-preview"
"""Primary Gemini model used for receipt tests."""

DEFAULT_GEMINI_FALLBACK_MODEL: Final[str] = "gemini-flash-lite-latest"
"""Fallback Gemini model used when the primary model is unavailable."""


def project_root() -> Path:
    """Return the SpendScan repository root."""
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for OCR and receipt analysis."""

    model_config = SettingsConfigDict(
        env_prefix="SPENDSCAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_prefix: str = "/api/v1"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = DEFAULT_GEMINI_MODEL
    gemini_fallback_model: str = DEFAULT_GEMINI_FALLBACK_MODEL
    gemini_temperature: float = 0.0
    gemini_max_output_tokens: int = 8192
    qianfan_model_dir: Path = Field(default=Path("external/models/ocr/qianfan-ocr"))
    llama_cache_dir: Path = Field(default=Path("external/bin/llama"))
    llama_build_tag: str | None = None

    @property
    def resolved_qianfan_model_dir(self) -> Path:
        """Return an absolute Qianfan model directory path."""
        return self._resolve_repo_path(self.qianfan_model_dir)

    @property
    def resolved_llama_cache_dir(self) -> Path:
        """Return an absolute llama.cpp binary cache directory path."""
        return self._resolve_repo_path(self.llama_cache_dir)

    @property
    def gemini_api_key_value(self) -> str:
        """Return the raw Gemini API key or an empty string."""
        if self.gemini_api_key is None:
            return ""
        return self.gemini_api_key.get_secret_value().strip()

    def _resolve_repo_path(self, path: Path) -> Path:
        """Resolve repository-relative paths against the project root."""
        if path.is_absolute():
            return path
        return project_root() / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load cached application settings."""
    return Settings()
