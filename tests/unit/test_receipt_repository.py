from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, select

from spendscan.db.repositories import ReceiptImageCreate, ReceiptRepository
from spendscan.llm import ReceiptAnalysisResult, ReceiptItem, ReceiptPipelineResult
from spendscan.models import (
    Budget,
    BudgetReceipt,
    Folder,
    FolderReceipt,
    Receipt,
    ReceiptImage,
)
from spendscan.models import (
    ReceiptItem as DbReceiptItem,
)


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


def test_receipt_repository_delete_removes_dependents_without_database_cascade(db_session: Session) -> None:
    repository = ReceiptRepository(db_session)
    detail = repository.save_analysis(
        result=ReceiptPipelineResult(
            ocr_text="OCR text",
            ocr_engine="fake-ocr",
            ocr_processing_time_ms=1.0,
            analysis=ReceiptAnalysisResult(
                merchant_name="Auchan",
                receipt_date="2026-05-21",
                total_amount=Decimal("9.99"),
                items=[ReceiptItem(name="Woda", total_price=Decimal("9.99"), category="drinks")],
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
    assert detail.receipt.id is not None

    folder = Folder(user_id=1, name="May")
    budget = Budget(user_id=1, name="Groceries", amount_limit=100, period_type="monthly")
    db_session.add(folder)
    db_session.add(budget)
    db_session.flush()
    assert folder.id is not None
    assert budget.id is not None
    db_session.add(FolderReceipt(folder_id=folder.id, receipt_id=detail.receipt.id))
    db_session.add(BudgetReceipt(budget_id=budget.id, receipt_id=detail.receipt.id))
    db_session.commit()

    deleted = repository.delete_receipt(detail.receipt.id)

    assert deleted is not None
    assert db_session.get(Receipt, detail.receipt.id) is None
    assert db_session.exec(select(ReceiptImage).where(ReceiptImage.receipt_id == detail.receipt.id)).all() == []
    assert db_session.exec(select(DbReceiptItem).where(DbReceiptItem.receipt_id == detail.receipt.id)).all() == []
    assert db_session.exec(select(FolderReceipt).where(FolderReceipt.receipt_id == detail.receipt.id)).all() == []
    assert db_session.exec(select(BudgetReceipt).where(BudgetReceipt.receipt_id == detail.receipt.id)).all() == []
