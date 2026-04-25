from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from spendscan.llm import ReceiptPipelineResult
from spendscan.pipeline import ReceiptPipeline

_RUN_E2E = os.environ.get("SPENDSCAN_RUN_E2E") == "1"
_INPUT_DIR = Path("workspace/input")
_EXPECTED_RECEIPT_COUNT = 3


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not _RUN_E2E, reason="Set SPENDSCAN_RUN_E2E=1 to run real OCR/Gemini receipt E2E.")
def test_receipt_pipeline_e2e_workspace_receipts() -> None:
    receipt_paths = tuple(sorted(_INPUT_DIR.glob("receipt_*.png")))

    assert len(receipt_paths) == _EXPECTED_RECEIPT_COUNT

    results = asyncio.run(_analyze_receipts(receipt_paths))

    assert len(results) == _EXPECTED_RECEIPT_COUNT
    for result in results:
        assert result.ocr_engine == "qianfan-ocr"
        assert result.analysis.currency == "PLN"
        assert result.analysis.raw_ocr_text == result.ocr_text


async def _analyze_receipts(receipt_paths: tuple[Path, ...]) -> list[ReceiptPipelineResult]:
    pipeline = ReceiptPipeline()
    try:
        return [await pipeline.analyze_image(receipt_path) for receipt_path in receipt_paths]
    finally:
        await pipeline.cleanup()
