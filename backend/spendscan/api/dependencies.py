"""FastAPI dependency providers and annotated dependency aliases.

Exports injectable provider functions and their ``Annotated`` shorthand types
for use as FastAPI path-operation dependencies:

- ``SettingsDep`` — application settings singleton.
- ``SessionDep`` — SQLModel database session per request.
- ``ReceiptPipelineDep`` — receipt pipeline reusing the shared OCR engine.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from spendscan.config import Settings, get_settings
from spendscan.db import get_session
from spendscan.llm import GeminiReceiptClient
from spendscan.ocr import OcrService, PaddleOcrConfig
from spendscan.pipeline import ReceiptPipeline

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_ocr_service(request: Request, settings: SettingsDep) -> OcrService:
    """Return the shared OcrService preloaded at app startup."""
    ocr = getattr(request.app.state, "ocr_service", None)
    if ocr is None:
        ocr = OcrService(PaddleOcrConfig.from_settings(settings))
        request.app.state.ocr_service = ocr
    return ocr


def get_receipt_pipeline(request: Request, settings: SettingsDep) -> ReceiptPipeline:
    """Create receipt pipeline reusing the shared OcrService."""
    ocr = get_ocr_service(request, settings)
    llm = GeminiReceiptClient(settings)
    return ReceiptPipeline(ocr=ocr, llm=llm)


ReceiptPipelineDep = Annotated[ReceiptPipeline, Depends(get_receipt_pipeline)]
