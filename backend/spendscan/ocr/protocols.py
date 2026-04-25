"""OCR protocols."""

from __future__ import annotations

from typing import Any, Protocol

from .types import ImageInput, OcrResult


class OcrEngine(Protocol):
    """Protocol implemented by OCR engines."""

    @property
    def name(self) -> str:
        """Human-readable engine name."""
        ...

    @property
    def is_available(self) -> bool:
        """Return whether the engine is initialized and ready."""
        ...

    def initialize(self, **kwargs: Any) -> None:
        """Initialize model/runtime resources."""
        ...

    def recognize(self, image: ImageInput, **kwargs: Any) -> OcrResult:
        """Extract text from an image."""
        ...

    def cleanup(self) -> None:
        """Release runtime resources."""
        ...
