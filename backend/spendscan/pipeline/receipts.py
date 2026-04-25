"""Receipt OCR -> LLM analysis pipeline."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Protocol

from spendscan.llm import GeminiReceiptClient, ReceiptAnalysisResult, ReceiptPipelineResult
from spendscan.ocr import ImageInput, OcrResult, OcrService


class ReceiptOcrService(Protocol):
    """OCR service required by the receipt pipeline."""

    async def recognize(self, image: ImageInput) -> OcrResult:
        """Recognize text in an image."""
        ...


class ReceiptLlmClient(Protocol):
    """LLM client required by the receipt pipeline."""

    async def analyze_receipt(self, *, ocr_text: str, image_path: Path | None = None) -> ReceiptAnalysisResult:
        """Analyze OCR text into receipt JSON."""
        ...


class ReceiptPipeline:
    """Minimal receipt analysis pipeline."""

    __slots__ = ("_llm", "_ocr")

    def __init__(self, *, ocr: ReceiptOcrService | None = None, llm: ReceiptLlmClient | None = None) -> None:
        self._ocr = ocr or OcrService()
        self._llm = llm or GeminiReceiptClient()

    async def recognize_image(self, image: ImageInput) -> OcrResult:
        """Run OCR only."""
        return await self._ocr.recognize(image)

    async def analyze_image(self, image_path: Path) -> ReceiptPipelineResult:
        """Run OCR and Gemini parsing for a receipt image."""
        ocr_result = await self._ocr.recognize(image_path)
        if ocr_result.error:
            analysis = ReceiptAnalysisResult(
                total_amount=Decimal("0"),
                raw_ocr_text=ocr_result.text,
                warnings=[ocr_result.error],
            )
        else:
            analysis = await self._llm.analyze_receipt(ocr_text=ocr_result.text, image_path=image_path)

        return ReceiptPipelineResult(
            ocr_text=ocr_result.text,
            ocr_engine=ocr_result.engine,
            ocr_processing_time_ms=ocr_result.processing_time_ms,
            analysis=analysis,
        )
