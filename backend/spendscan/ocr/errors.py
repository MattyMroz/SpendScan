"""OCR domain errors."""

from __future__ import annotations

from spendscan.errors import ConfigurationError, ExternalServiceError, SpendScanError


class OcrError(SpendScanError):
    """Base error for OCR failures."""


class OcrConfigError(OcrError, ConfigurationError):
    """OCR configuration is missing or invalid."""


class OcrEngineError(OcrError, ExternalServiceError):
    """OCR engine failed during image recognition."""
