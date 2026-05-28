from __future__ import annotations

import asyncio
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

import pytest

from spendscan.errors import ExternalServiceError
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


class FailingOcr:
    async def recognize(self, image: ImageInput) -> OcrResult:
        return OcrResult(
            text="",
            lines=[],
            engine="fake-ocr",
            processing_time_ms=0.5,
            image_shape=(0, 0),
            error=f"engine boom for {Path(str(image)).name}",
        )


class FakeLlm:
    def __init__(self) -> None:
        self.image_paths: tuple[Path, ...] = ()

    async def analyze_receipt(
        self,
        *,
        ocr_text: str,
        image_path: Path | None = None,
        image_paths: Sequence[Path] | None = None,
    ) -> ReceiptAnalysisResult:
        self.image_paths = tuple(image_paths or (() if image_path is None else (image_path,)))
        return ReceiptAnalysisResult(total_amount=Decimal("12.50"), raw_ocr_text=ocr_text)


def test_receipt_pipeline_runs_ocr_then_llm() -> None:
    pipeline = ReceiptPipeline(ocr=FakeOcr(), llm=FakeLlm())

    result = asyncio.run(pipeline.analyze_image(Path("receipt.png")))

    assert result.ocr_engine == "fake-ocr"
    assert result.analysis.total_amount == Decimal("12.50")
    assert result.analysis.raw_ocr_text == "TOTAL 12.50 from receipt.png"


def test_receipt_pipeline_combines_multi_image_receipt() -> None:
    llm = FakeLlm()
    pipeline = ReceiptPipeline(ocr=FakeOcr(), llm=llm)

    result = asyncio.run(pipeline.analyze_images((Path("receipt_001_1.png"), Path("receipt_001_2.png"))))

    assert result.receipt.ocr_engine == "fake-ocr"
    assert result.receipt.ocr_processing_time_ms == 2.0
    assert result.receipt.analysis.raw_ocr_text == result.receipt.ocr_text
    assert "--- PAGE 1: receipt_001_1.png ---" in result.receipt.ocr_text
    assert "--- PAGE 2: receipt_001_2.png ---" in result.receipt.ocr_text
    assert llm.image_paths == (Path("receipt_001_1.png"), Path("receipt_001_2.png"))
    assert [image.page_number for image in result.images] == [1, 2]


def test_receipt_pipeline_analyzes_multiple_receipt_groups() -> None:
    pipeline = ReceiptPipeline(ocr=FakeOcr(), llm=FakeLlm())

    results = asyncio.run(
        pipeline.analyze_receipt_groups(
            (
                (Path("receipt_001_1.png"), Path("receipt_001_2.png")),
                (Path("receipt_002_1.png"), Path("receipt_002_2.png")),
            )
        )
    )

    assert len(results) == 2
    assert [len(result.images) for result in results] == [2, 2]
    assert "--- PAGE 2: receipt_002_2.png ---" in results[1].receipt.ocr_text


def test_receipt_pipeline_raises_when_all_ocr_pages_fail() -> None:
    pipeline = ReceiptPipeline(ocr=FailingOcr(), llm=FakeLlm())

    with pytest.raises(ExternalServiceError, match="All OCR pages failed"):
        asyncio.run(pipeline.analyze_images((Path("page_1.png"), Path("page_2.png"))))


class _OcrSequence:
    def __init__(self, results: list[OcrResult]) -> None:
        self._results = list(results)

    async def recognize(self, image: ImageInput) -> OcrResult:
        return self._results.pop(0)


def test_receipt_pipeline_keeps_partial_ocr_fallback() -> None:
    llm = FakeLlm()
    ocr = _OcrSequence(
        [
            OcrResult(
                text="TOTAL 9.99",
                lines=[OcrLine(text="TOTAL 9.99")],
                engine="fake-ocr",
                processing_time_ms=1.0,
                image_shape=(1, 1),
            ),
            OcrResult(
                text="",
                lines=[],
                engine="fake-ocr",
                processing_time_ms=0.5,
                image_shape=(0, 0),
                error="boom",
            ),
        ]
    )
    pipeline = ReceiptPipeline(ocr=ocr, llm=llm)

    result = asyncio.run(pipeline.analyze_images((Path("page_1.png"), Path("page_2.png"))))

    assert result.receipt.analysis.total_amount == Decimal("0")
    assert result.receipt.analysis.warnings == ["page 2: boom"]
