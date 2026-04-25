"""OCR utility exports."""

from __future__ import annotations

from .memory import cleanup_gpu_memory, get_fallback_dimension
from .postprocessing import parse_ocr_output
from .preprocessing import convert_to_pil, validate_and_resize_image

__all__ = [
    "cleanup_gpu_memory",
    "convert_to_pil",
    "get_fallback_dimension",
    "parse_ocr_output",
    "validate_and_resize_image",
]
