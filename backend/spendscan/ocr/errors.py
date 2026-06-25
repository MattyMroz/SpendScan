"""OCR domain error hierarchy.

All OCR errors inherit from ``OcrError`` so callers can catch the entire
subtree with a single ``except OcrError``.  Subclasses also mix in the
appropriate application-level base (``ConfigurationError`` or
``ExternalServiceError``) for cross-domain error handling.
"""

from __future__ import annotations

from spendscan.errors import ConfigurationError, ExternalServiceError, SpendScanError


class OcrError(SpendScanError):
    """Base error for all OCR subsystem failures."""


class OcrConfigError(OcrError, ConfigurationError):
    """OCR configuration is missing or invalid.

    Raised when required model files or directories are not configured
    or cannot be located on disk.
    """


class OcrEngineError(OcrError, ExternalServiceError):
    """OCR engine encountered a runtime failure during image recognition.

    Raised when the underlying inference process fails, crashes, or
    returns an unrecoverable error (e.g. GPU OOM exhausted all retries).
    """
