"""Structural protocols for OCR engine implementations.

Any class that satisfies the ``OcrEngine`` interface can be used as a
drop-in backend without inheriting from a base class.
"""

from __future__ import annotations

from typing import Any, Protocol

from .types import ImageInput, OcrResult


class OcrEngine(Protocol):
    """Structural protocol for synchronous OCR engine backends.

    Implementors provide model initialization, single-image recognition,
    and resource cleanup.  ``OcrService`` depends on this protocol so
    alternative engines can be injected for testing or experimentation.
    """

    @property
    def name(self) -> str:
        """Human-readable engine identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether the engine is initialized and ready to process images."""
        ...

    def initialize(self, **kwargs: Any) -> None:
        """Load model weights and start any required runtime processes.

        Args:
            **kwargs: Backend-specific initialization options.
        """
        ...

    def recognize(self, image: ImageInput, **kwargs: Any) -> OcrResult:
        """Extract text from an image.

        Args:
            image: Image to process — file path, numpy array, or PIL image.
            **kwargs: Backend-specific inference options.

        Returns:
            OCR result containing extracted text and per-line details.
        """
        ...

    def cleanup(self) -> None:
        """Release model weights and runtime resources."""
        ...
