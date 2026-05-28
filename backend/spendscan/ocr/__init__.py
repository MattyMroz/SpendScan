"""OCR package exports."""

from __future__ import annotations

from .paddle import PADDLE_MMPROJ_HF_REPO, PADDLE_MODEL_HF_REPO, PaddleModelResolver, PaddleOcrConfig, PaddleOcrEngine
from .qianfan import QIANFAN_HF_REPO, QianfanModelResolver, QianfanOcrConfig, QianfanOcrEngine
from .service import OcrService
from .types import ImageInput, OcrLine, OcrResult

__all__ = [
    "PADDLE_MMPROJ_HF_REPO",
    "PADDLE_MODEL_HF_REPO",
    "QIANFAN_HF_REPO",
    "ImageInput",
    "OcrLine",
    "OcrResult",
    "OcrService",
    "PaddleModelResolver",
    "PaddleOcrConfig",
    "PaddleOcrEngine",
    "QianfanModelResolver",
    "QianfanOcrConfig",
    "QianfanOcrEngine",
]
