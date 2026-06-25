"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_GEMINI_MODEL: Final[str] = "gemini-3.1-flash-lite-preview"
"""Primary Gemini model used for receipt tests."""

DEFAULT_GEMINI_FALLBACK_MODEL: Final[str] = "gemini-flash-lite-latest"
"""Fallback Gemini model used when the primary model is unavailable."""

DEFAULT_GEMINI_GEMMA_FALLBACK_MODEL: Final[str] = "gemma-4-31b-it"
"""Last-resort Gemma model used when Gemini Flash Lite models are unavailable."""

DEFAULT_DATABASE_URL: Final[str] = "postgresql+psycopg://postgres:postgres@localhost:5432/spendscan"
"""Default local PostgreSQL database URL for the demo environment."""

DEFAULT_LLAMA_BUILD_TAG: Final[str] = "b9383"
"""Pinned llama.cpp build used for the local PaddleOCR-VL runtime."""


def project_root() -> Path:
    """Return the SpendScan repository root."""
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for OCR and receipt analysis.

    Loaded from environment variables with the ``SPENDSCAN_`` prefix and
    from an optional ``.env`` file. Extra environment keys are silently
    ignored.

    Attributes:
        api_prefix: URL prefix for all API routes.
        gemini_api_key: Primary Gemini API key (secret).
        gemini_api_key_backup: Backup Gemini API key (secret).
        gemini_model: Primary Gemini model identifier.
        gemini_fallback_model: Fallback model when the primary is unavailable.
        gemini_gemma_fallback_model: Last-resort Gemma model identifier.
        gemini_temperature: Sampling temperature; 0.0 = deterministic.
        gemini_max_output_tokens: Maximum tokens in a single Gemini response.
        gemini_thinking_budget: Token budget for extended thinking; 0 disables it.
        gemini_retry_attempts: Number of retry attempts on transient errors.
        gemini_retry_delay_seconds: Initial delay between retries in seconds.
        gemini_timeout_seconds: Per-request timeout for Gemini calls in seconds.
        paddle_model_dir: Path to PaddleOCR-VL model weights (repo-relative or absolute).
        llama_cache_dir: Path to llama.cpp binary cache (repo-relative or absolute).
        llama_build_tag: Pinned llama.cpp build tag; blank env value resets to default.
        database_url: PostgreSQL connection URL (secret).
        upload_dir: Directory for uploaded receipt images (repo-relative or absolute).
        jwt_secret: Secret key used to sign JWTs (secret).
        jwt_algorithm: JWT signing algorithm.
        jwt_expires_minutes: JWT lifetime in minutes.
        auth_cookie_name: Name of the HttpOnly authentication cookie.
        auth_cookie_secure: Whether the auth cookie requires HTTPS.
        auth_cookie_samesite: SameSite policy for the auth cookie.
    """

    model_config = SettingsConfigDict(
        env_prefix="SPENDSCAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_prefix: str = "/api/v1"
    gemini_api_key: SecretStr | None = None
    gemini_api_key_backup: SecretStr | None = None
    gemini_model: str = DEFAULT_GEMINI_MODEL
    gemini_fallback_model: str = DEFAULT_GEMINI_FALLBACK_MODEL
    gemini_gemma_fallback_model: str = DEFAULT_GEMINI_GEMMA_FALLBACK_MODEL
    gemini_temperature: float = 0.0
    gemini_max_output_tokens: int = 8192
    gemini_thinking_budget: int | None = Field(default=0, ge=0)
    gemini_retry_attempts: int = Field(default=3, ge=1)
    gemini_retry_delay_seconds: float = Field(default=5.0, ge=0)
    gemini_timeout_seconds: float = Field(default=60.0, gt=0)
    paddle_model_dir: Path = Field(default=Path("external/models/ocr/paddle-ocr"))
    llama_cache_dir: Path = Field(default=Path("external/bin/llama"))
    llama_build_tag: str | None = DEFAULT_LLAMA_BUILD_TAG
    database_url: SecretStr = SecretStr(DEFAULT_DATABASE_URL)
    upload_dir: Path = Field(default=Path("workspace/uploads/receipts"))
    jwt_secret: SecretStr = SecretStr("dev-only-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = Field(default=60 * 24, gt=0)
    auth_cookie_name: str = "ss_access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    @field_validator("llama_build_tag", mode="before")
    @classmethod
    def normalize_llama_build_tag(cls, value: object) -> str:
        """Treat a blank env value as the project's pinned llama.cpp build."""
        if value is None:
            return DEFAULT_LLAMA_BUILD_TAG
        if isinstance(value, str) and not value.strip():
            return DEFAULT_LLAMA_BUILD_TAG
        return str(value)

    @property
    def resolved_paddle_model_dir(self) -> Path:
        """Return an absolute PaddleOCR-VL model directory path."""
        return self._resolve_repo_path(self.paddle_model_dir)

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

    @property
    def gemini_api_key_backup_value(self) -> str:
        """Return the raw backup Gemini API key or an empty string."""
        if self.gemini_api_key_backup is None:
            return ""
        return self.gemini_api_key_backup.get_secret_value().strip()

    @property
    def database_url_value(self) -> str:
        """Return the raw database URL."""
        return self.database_url.get_secret_value().strip()

    @property
    def jwt_secret_value(self) -> str:
        """Return the raw JWT signing secret."""
        return self.jwt_secret.get_secret_value()

    @property
    def resolved_upload_dir(self) -> Path:
        """Return an absolute upload directory path."""
        return self._resolve_repo_path(self.upload_dir)

    def _resolve_repo_path(self, path: Path) -> Path:
        """Resolve repository-relative paths against the project root."""
        if path.is_absolute():
            return path
        return project_root() / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load cached application settings."""
    return Settings()
