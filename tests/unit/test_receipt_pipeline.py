from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

from spendscan.llm import ReceiptAnalysisResult
from spendscan.ocr import ImageInput, OcrLine, OcrResult
from spendscan.pipeline import ReceiptPipeline


class FakeOcr:
    async def recognize(self, image: ImageInput) -> OcrResult:
        return OcrResult(
            text=f"TOTAL 12.50 from {Path(str(image)).name}",
            lines=[OcrLine(text="TOTAL 12.50")],
            engine="fake-ocr",
            processing_time_ms=1.0,
            image_shape=(100, 100),
        )


class FakeLlm:
    async def analyze_receipt(self, *, ocr_text: str, image_path: Path | None = None) -> ReceiptAnalysisResult:
        return ReceiptAnalysisResult(total_amount=Decimal("12.50"), raw_ocr_text=ocr_text)


def test_receipt_pipeline_runs_ocr_then_llm() -> None:
    pipeline = ReceiptPipeline(ocr=FakeOcr(), llm=FakeLlm())

    result = asyncio.run(pipeline.analyze_image(Path("receipt.png")))

    assert result.ocr_engine == "fake-ocr"
    assert result.analysis.total_amount == Decimal("12.50")
    assert result.analysis.raw_ocr_text == "TOTAL 12.50 from receipt.png"
