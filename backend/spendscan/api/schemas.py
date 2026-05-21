"""API response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

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
    stored_path: str
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
    image_count: int = 0
    item_count: int = 0
    created_at: datetime | None


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
    raw_ocr_text: str
    warnings: list[str]
    error: str | None
    created_at: datetime | None
    images: list[StoredReceiptImageResponse]
    items: list[StoredReceiptItemResponse]


class ReceiptBatchCreateResponse(BaseModel):
    """Response for a batch upload of separate receipts."""

    model_config = ConfigDict(extra="forbid")
    receipts: list[ReceiptDetailResponse]
