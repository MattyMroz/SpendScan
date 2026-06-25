"""OCR domain types: image input aliases and recognition result dataclasses."""

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
    """Single recognized text line from OCR output.

    Attributes:
        text: Recognized text content of the line.
        confidence: Recognition confidence score in the range [0.0, 1.0].
        bbox: Bounding box as (x, y, width, height) in pixels, or ``None``
            when the engine does not provide spatial information.
    """

    text: str
    confidence: float = 1.0
    bbox: tuple[int, int, int, int] | None = None


@dataclass(slots=True)
class OcrResult:
    """Complete OCR result for a single processed image.

    Attributes:
        text: Full recognized text, joined from all lines.
        lines: Per-line recognition results in document order.
        engine: Identifier of the engine that produced this result.
        processing_time_ms: Inference duration in milliseconds.
        init_time_ms: Engine initialization time in milliseconds (0 when
            the engine was already warm).
        image_shape: Source image dimensions as (height, width) in pixels.
        error: Human-readable error message when recognition failed,
            ``None`` on success.
    """

    text: str = ""
    lines: list[OcrLine] = field(default_factory=list)
    engine: str = ""
    processing_time_ms: float = 0.0
    init_time_ms: float = 0.0
    image_shape: tuple[int, int] = (0, 0)
    error: str | None = None

    @property
    def is_success(self) -> bool:
        """Whether OCR completed without an engine error."""
        return self.error is None

    @property
    def is_empty(self) -> bool:
        """Whether no text was extracted from the image."""
        return not self.text.strip()

    @property
    def line_count(self) -> int:
        """Number of recognized text lines."""
        return len(self.lines)
