"""OCR package exports."""

from __future__ import annotations

from .qianfan import QIANFAN_HF_REPO, QianfanModelResolver, QianfanOcrConfig, QianfanOcrEngine
from .service import OcrService
from .types import ImageInput, OcrLine, OcrResult

__all__ = [
    "QIANFAN_HF_REPO",
    "ImageInput",
    "OcrLine",
    "OcrResult",
    "OcrService",
    "QianfanModelResolver",
    "QianfanOcrConfig",
    "QianfanOcrEngine",
]
