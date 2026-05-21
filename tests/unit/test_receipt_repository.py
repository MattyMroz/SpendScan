from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session

from spendscan.db.repositories import ReceiptImageCreate, ReceiptRepository
from spendscan.llm import ReceiptAnalysisResult, ReceiptItem, ReceiptPipelineResult


def test_receipt_repository_saves_analysis_images_items_and_categories(db_session: Session) -> None:
    repository = ReceiptRepository(db_session)
    result = ReceiptPipelineResult(
        ocr_text="OCR text",
        ocr_engine="fake-ocr",
        ocr_processing_time_ms=2.0,
        analysis=ReceiptAnalysisResult(
            merchant_name="Biedronka",
            receipt_date="2026-05-21",
            total_amount=Decimal("12.50"),
            items=[
                ReceiptItem(
                    name="Mleko",
                    quantity=Decimal("1"),
                    unit_price=Decimal("12.50"),
                    total_price=Decimal("12.50"),
                    category="food",
                )
            ],
            raw_ocr_text="OCR text",
        ),
    )

    detail = repository.save_analysis(
        result=result,
        images=(
            ReceiptImageCreate(
                page_number=1,
                original_filename="receipt_001_1.png",
                stored_path=Path("workspace/uploads/receipt_001_1.png"),
                content_type="image/png",
                ocr_text="OCR text",
                ocr_engine="fake-ocr",
                ocr_processing_time_ms=2.0,
                image_shape=(100, 200),
            ),
        ),
    )

    assert detail.receipt.id is not None
    assert detail.receipt.merchant_name == "Biedronka"
    assert detail.images[0].stored_path == "workspace/uploads/receipt_001_1.png"
    assert detail.images[0].image_height == 100
    assert detail.images[0].image_width == 200
    assert detail.items[0].item.product_name == "Mleko"
    assert detail.items[0].category_name == "food"


def test_receipt_repository_converts_saved_receipts_to_dashboard_inputs(db_session: Session) -> None:
    repository = ReceiptRepository(db_session)
    repository.save_analysis(
        result=ReceiptPipelineResult(
            ocr_text="OCR text",
            ocr_engine="fake-ocr",
            ocr_processing_time_ms=1.0,
            analysis=ReceiptAnalysisResult(
                merchant_name="Lidl",
                receipt_date="2026-05-21",
                total_amount=Decimal("20.00"),
                items=[ReceiptItem(name="Chleb", total_price=Decimal("20.00"), category="food")],
                raw_ocr_text="OCR text",
            ),
        ),
        images=(
            ReceiptImageCreate(
                page_number=1,
                original_filename="receipt.png",
                stored_path=Path("workspace/uploads/receipt.png"),
                content_type="image/png",
                ocr_text="OCR text",
                ocr_engine="fake-ocr",
                ocr_processing_time_ms=1.0,
                image_shape=(100, 100),
            ),
        ),
    )

    results = repository.list_analysis_results(start_date=date(2026, 5, 1), end_date=date(2026, 5, 31))

    assert len(results) == 1
    assert results[0].merchant_name == "Lidl"
    assert results[0].items[0].category == "food"
