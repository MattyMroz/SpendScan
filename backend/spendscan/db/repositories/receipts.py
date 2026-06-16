"""Receipt persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Final

from sqlmodel import Session, col, select

from spendscan.llm import ReceiptAnalysisResult, ReceiptPipelineResult
from spendscan.llm import ReceiptItem as AnalysisReceiptItem
from spendscan.models import BudgetReceipt, Category, FolderReceipt, Receipt, ReceiptImage, ReceiptItem, User

DEMO_USER_ID: Final[int] = 1
"""Single demo user used until authentication exists."""

CENTS_PER_UNIT: Final[int] = 100


def decimal_to_cents(value: Decimal | None) -> int | None:
    """Convert a decimal currency value to integer cents."""
    if value is None:
        return None
    return int((value * CENTS_PER_UNIT).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def required_decimal_to_cents(value: Decimal) -> int:
    """Convert a required decimal currency value to integer cents."""
    return decimal_to_cents(value) or 0


def cents_to_decimal(value: int | None) -> Decimal | None:
    """Convert integer cents to decimal currency value."""
    if value is None:
        return None
    return Decimal(value) / CENTS_PER_UNIT


def required_cents_to_decimal(value: int) -> Decimal:
    """Convert required integer cents to decimal currency value."""
    return Decimal(value) / CENTS_PER_UNIT


@dataclass(frozen=True, slots=True)
class ReceiptImageCreate:
    """Data needed to persist one receipt image page."""

    page_number: int
    original_filename: str
    stored_path: Path | None  # now optional — None when stored in DB
    content_type: str | None
    ocr_text: str
    ocr_engine: str
    ocr_processing_time_ms: float
    image_shape: tuple[int, int]
    image_data: bytes | None = None  # raw image bytes to store in the DB


@dataclass(frozen=True, slots=True)
class ReceiptItemRecord:
    """Persisted receipt item with optional category name."""

    item: ReceiptItem
    category_name: str | None


@dataclass(frozen=True, slots=True)
class ReceiptDetailRecord:
    """Persisted receipt aggregate."""

    receipt: Receipt
    images: tuple[ReceiptImage, ...]
    items: tuple[ReceiptItemRecord, ...]


class ReceiptRepository:
    """Database access for receipt demo workflows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def ensure_demo_user(self) -> User:
        """Create and return the demo user when it does not exist."""
        user = self._session.get(User, DEMO_USER_ID)
        if user is not None:
            return user
        user = User(id=DEMO_USER_ID, username="demo", email="demo@spendscan.local", password_hash="demo")  # noqa: S106
        self._session.add(user)
        self._session.flush()
        return user

    def save_analysis(
        self,
        *,
        result: ReceiptPipelineResult,
        images: tuple[ReceiptImageCreate, ...],
        user_id: int = DEMO_USER_ID,
    ) -> ReceiptDetailRecord:
        """Persist a pipeline result and return the saved aggregate."""
        self.ensure_demo_user()
        analysis = result.analysis
        receipt = Receipt(
            user_id=user_id,
            status="completed",
            merchant_name=analysis.merchant_name,
            receipt_date=analysis.receipt_date,
            currency=analysis.currency,
            subtotal_amount=decimal_to_cents(analysis.subtotal_amount),
            tax_amount=decimal_to_cents(analysis.tax_amount),
            total_amount=required_decimal_to_cents(analysis.total_amount),
            total_discount_amount=decimal_to_cents(analysis.total_discount_amount),
            payment_method=analysis.payment_method,
            raw_ocr_text=result.ocr_text,
            warnings=analysis.warnings,
        )
        self._session.add(receipt)
        self._session.flush()
        if receipt.id is None:
            msg = "Receipt id was not assigned after flush"
            raise RuntimeError(msg)

        for image in images:
            height, width = image.image_shape
            self._session.add(
                ReceiptImage(
                    receipt_id=receipt.id,
                    page_number=image.page_number,
                    original_filename=image.original_filename,
                    stored_path=image.stored_path.as_posix() if image.stored_path else None,
                    image_data=image.image_data,
                    content_type=image.content_type,
                    ocr_text=image.ocr_text,
                    ocr_engine=image.ocr_engine,
                    ocr_processing_time_ms=image.ocr_processing_time_ms,
                    image_width=width if width > 0 else None,
                    image_height=height if height > 0 else None,
                )
            )

        for item in analysis.items:
            category = self._get_or_create_category(item.category)
            self._session.add(
                ReceiptItem(
                    receipt_id=receipt.id,
                    product_name=item.name,
                    quantity=item.quantity,
                    unit_price=decimal_to_cents(item.unit_price),
                    total_price=required_decimal_to_cents(item.total_price),
                    discount_amount=decimal_to_cents(item.discount_amount),
                    category_id=category.id if category is not None else None,
                )
            )

        self._session.commit()
        return self.get_detail(receipt.id, user_id=user_id) or ReceiptDetailRecord(receipt=receipt, images=(), items=())

    def list_receipts(
        self,
        *,
        user_id: int = DEMO_USER_ID,
        start_date: date | None = None,
        end_date: date | None = None,
        merchant_name: str | None = None,
    ) -> list[Receipt]:
        """Return persisted receipts filtered for the demo user."""
        statement = select(Receipt).where(Receipt.user_id == user_id)
        if start_date is not None:
            statement = statement.where(col(Receipt.receipt_date) >= start_date)
        if end_date is not None:
            statement = statement.where(col(Receipt.receipt_date) <= end_date)
        if merchant_name:
            statement = statement.where(col(Receipt.merchant_name).ilike(f"%{merchant_name.strip()}%"))
        statement = statement.order_by(col(Receipt.created_at).desc(), col(Receipt.id).desc())
        return list(self._session.exec(statement).all())

    def get_detail(self, receipt_id: int, *, user_id: int = DEMO_USER_ID) -> ReceiptDetailRecord | None:
        """Return one persisted receipt aggregate."""
        receipt = self._session.get(Receipt, receipt_id)
        if receipt is None or receipt.user_id != user_id:
            return None
        images = tuple(
            self._session.exec(
                select(ReceiptImage)
                .where(ReceiptImage.receipt_id == receipt_id)
                .order_by(col(ReceiptImage.page_number).asc())
            ).all()
        )
        item_rows = self._session.exec(
            select(ReceiptItem, Category.name)
            .join(Category, isouter=True)
            .where(ReceiptItem.receipt_id == receipt_id)
            .order_by(col(ReceiptItem.id).asc())
        ).all()
        items = tuple(ReceiptItemRecord(item=item, category_name=category_name) for item, category_name in item_rows)
        return ReceiptDetailRecord(receipt=receipt, images=images, items=items)

    def delete_receipt(self, receipt_id: int, *, user_id: int = DEMO_USER_ID) -> ReceiptDetailRecord | None:
        """Delete a receipt aggregate and return its previous state."""
        detail = self.get_detail(receipt_id, user_id=user_id)
        if detail is None:
            return None
        self._delete_receipt_dependents(detail)
        self._session.delete(detail.receipt)
        self._session.commit()
        return detail

    def update_receipt(
        self,
        receipt_id: int,
        *,
        user_id: int,
        merchant_name: str | None = None,
        receipt_date: date | None = None,
        currency: str | None = None,
        total_amount: Decimal | None = None,
        payment_method: str | None = None,
        description: str | None = None,
        importance: int | None = None,
        items: list[dict[str, object]] | None = None,
    ) -> ReceiptDetailRecord | None:
        """Patch editable fields of a receipt and optionally replace its items."""
        receipt = self._session.get(Receipt, receipt_id)
        if receipt is None or receipt.user_id != user_id:
            return None
        if merchant_name is not None:
            receipt.merchant_name = merchant_name or None
        if receipt_date is not None:
            receipt.receipt_date = receipt_date
        if currency is not None and currency.strip():
            receipt.currency = currency.strip().upper()
        if total_amount is not None:
            receipt.total_amount = required_decimal_to_cents(total_amount)
        if payment_method is not None:
            receipt.payment_method = payment_method or None
        if description is not None:
            receipt.description = description or None
        if importance is not None:
            receipt.importance = max(0, min(3, int(importance)))
        self._session.add(receipt)

        if items is not None:
            existing = self._session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).all()
            for old in existing:
                self._session.delete(old)
            self._session.flush()
            for payload in items:
                self._session.add(
                    ReceiptItem(
                        receipt_id=receipt_id,
                        product_name=str(payload.get("product_name") or "").strip() or "—",
                        quantity=payload.get("quantity"),
                        unit_price=payload.get("unit_price"),
                        total_price=payload.get("total_price"),
                        discount_amount=payload.get("discount_amount"),
                    )
                )

        self._session.commit()
        return self.get_detail(receipt_id, user_id=user_id)

    def list_analysis_results(
        self,
        *,
        start_date: date,
        end_date: date,
        user_id: int = DEMO_USER_ID,
    ) -> list[ReceiptAnalysisResult]:
        """Return persisted receipts converted back to dashboard input schemas."""
        receipts = self.list_receipts(user_id=user_id, start_date=start_date, end_date=end_date)
        results: list[ReceiptAnalysisResult] = []
        for receipt in receipts:
            if receipt.id is None:
                continue
            detail = self.get_detail(receipt.id, user_id=user_id)
            if detail is None or detail.receipt.status != "completed":
                continue
            results.append(_analysis_from_detail(detail))
        return results

    def _get_or_create_category(self, name: str | None) -> Category | None:
        normalized_name = (name or "").strip().lower()
        if not normalized_name:
            return None
        category = self._session.exec(select(Category).where(Category.name == normalized_name)).first()
        if category is not None:
            return category
        category = Category(name=normalized_name)
        self._session.add(category)
        self._session.flush()
        return category

    def _delete_receipt_dependents(self, detail: ReceiptDetailRecord) -> None:
        """Delete child rows explicitly so receipt removal does not depend on DB-level cascades."""
        receipt_id = detail.receipt.id
        if receipt_id is None:
            return

        folder_links = self._session.exec(select(FolderReceipt).where(FolderReceipt.receipt_id == receipt_id)).all()
        budget_links = self._session.exec(select(BudgetReceipt).where(BudgetReceipt.receipt_id == receipt_id)).all()

        for child in (*folder_links, *budget_links, *detail.images):
            self._session.delete(child)
        for item in detail.items:
            self._session.delete(item.item)
        self._session.flush()


def _analysis_from_detail(detail: ReceiptDetailRecord) -> ReceiptAnalysisResult:
    receipt = detail.receipt

    items = [
        AnalysisReceiptItem(
            name=item.item.product_name,
            quantity=item.item.quantity,
            unit_price=cents_to_decimal(item.item.unit_price),
            total_price=required_cents_to_decimal(item.item.total_price),
            discount_amount=cents_to_decimal(item.item.discount_amount),
            category=item.category_name,
        )
        for item in detail.items
    ]

    return ReceiptAnalysisResult(
        merchant_name=receipt.merchant_name,
        receipt_date=receipt.receipt_date,
        currency=receipt.currency,
        subtotal_amount=cents_to_decimal(receipt.subtotal_amount),
        tax_amount=cents_to_decimal(receipt.tax_amount),
        total_amount=required_cents_to_decimal(receipt.total_amount),
        total_discount_amount=cents_to_decimal(receipt.total_discount_amount),
        payment_method=receipt.payment_method,
        items=items,
        warnings=receipt.warnings,
        raw_ocr_text=receipt.raw_ocr_text,
    )
