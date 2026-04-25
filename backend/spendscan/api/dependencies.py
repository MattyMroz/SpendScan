"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from spendscan.config import Settings, get_settings
from spendscan.llm import GeminiReceiptClient
from spendscan.ocr import OcrService, QianfanOcrConfig
from spendscan.pipeline import ReceiptPipeline

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_receipt_pipeline(settings: SettingsDep) -> ReceiptPipeline:
    """Create receipt pipeline from current settings."""
    ocr = OcrService(QianfanOcrConfig.from_settings(settings))
    llm = GeminiReceiptClient(settings)
    return ReceiptPipeline(ocr=ocr, llm=llm)


ReceiptPipelineDep = Annotated[ReceiptPipeline, Depends(get_receipt_pipeline)]
