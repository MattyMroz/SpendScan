"""OCR result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PIL import Image

type ImageArray = npt.NDArray[np.uint8]
"""Image array accepted by OCR helpers."""

type ImageInput = str | Path | ImageArray | Image.Image
"""Supported image input types for OCR."""


@dataclass(frozen=True, slots=True)
class OcrLine:
    """Single recognized text line."""

    text: str
    confidence: float = 1.0
    bbox: tuple[int, int, int, int] | None = None


@dataclass(slots=True)
class OcrResult:
    """OCR result for one image."""

    text: str = ""
    lines: list[OcrLine] = field(default_factory=list)
    engine: str = ""
    processing_time_ms: float = 0.0
    init_time_ms: float = 0.0
    image_shape: tuple[int, int] = (0, 0)
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Return whether OCR completed without an engine error."""
        return self.error is None

    @property
    def is_empty(self) -> bool:
        """Return whether no text was extracted."""
        return not self.text.strip()

    @property
    def line_count(self) -> int:
        """Return number of recognized lines."""
        return len(self.lines)
