"""API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from spendscan.llm import ReceiptPipelineResult


class OcrLineResponse(BaseModel):
    """OCR line returned by the API."""

    model_config = ConfigDict(extra="forbid")
    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None


class OcrResponse(BaseModel):
    """OCR debug endpoint response."""

    model_config = ConfigDict(extra="forbid")
    text: str
    lines: list[OcrLineResponse]
    engine: str
    processing_time_ms: float
    image_shape: tuple[int, int]
    error: str | None = None


class ReadinessResponse(BaseModel):
    """Health readiness response."""

    model_config = ConfigDict(extra="forbid")
    ready: bool
    checks: dict[str, bool]


class ReceiptAnalyzeResponse(ReceiptPipelineResult):
    """Full receipt analysis endpoint response."""


class StoredReceiptImageResponse(BaseModel):
    """Persisted receipt image page response."""

    model_config = ConfigDict(extra="forbid")
    id: int
    page_number: int
    original_filename: str
    stored_path: str        # empty string "" for DB-stored images — kept for API compatibility
    content_type: str | None
    ocr_text: str
    ocr_engine: str
    ocr_processing_time_ms: float
    image_width: int | None
    image_height: int | None    


class StoredReceiptItemResponse(BaseModel):
    """Persisted receipt item response."""

    model_config = ConfigDict(extra="forbid")
    id: int
    product_name: str
    quantity: Decimal | None
    unit_price: Decimal | None
    total_price: Decimal
    discount_amount: Decimal | None
    category: str | None


class ReceiptListItemResponse(BaseModel):
    """Persisted receipt list item response."""

    model_config = ConfigDict(extra="forbid")

    id: int
    status: str
    merchant_name: str | None
    receipt_date: date | None
    currency: str
    total_amount: Decimal

    importance: int = 0
    image_count: int = 0
    item_count: int = 0

    created_at: datetime | None
    description: str | None = None

    folder_ids: list[int] = []


class ReceiptDetailResponse(BaseModel):
    """Persisted receipt detail response."""

    model_config = ConfigDict(extra="forbid")
    id: int
    status: str
    merchant_name: str | None
    receipt_date: date | None
    currency: str
    subtotal_amount: Decimal | None
    tax_amount: Decimal | None
    total_amount: Decimal
    total_discount_amount: Decimal | None
    payment_method: str | None
    description: str | None = None
    raw_ocr_text: str
    warnings: list[str]
    error: str | None
    importance: int = 0
    created_at: datetime | None
    images: list[StoredReceiptImageResponse]
    items: list[StoredReceiptItemResponse]


class ReceiptItemUpdate(BaseModel):
    """Editable fields of a receipt item."""

    model_config = ConfigDict(extra="forbid")
    id: int | None = None
    product_name: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal
    discount_amount: Decimal | None = None


class ReceiptUpdateRequest(BaseModel):
    """Editable fields of a saved receipt."""

    model_config = ConfigDict(extra="forbid")
    merchant_name: str | None = None
    receipt_date: date | None = None
    currency: str | None = None
    total_amount: Decimal | None = None
    payment_method: str | None = None
    description: str | None = None
    importance: int | None = Field(default=None, ge=0, le=3)
    items: list[ReceiptItemUpdate] | None = None


class ReceiptBatchCreateResponse(BaseModel):
    """Response for a batch upload of separate receipts."""

    model_config = ConfigDict(extra="forbid")
    receipts: list[ReceiptDetailResponse]
