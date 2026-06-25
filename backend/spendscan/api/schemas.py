"""Pydantic response schemas for the SpendScan REST API.

All schemas use ``extra="forbid"`` to reject unexpected fields and keep the
API surface explicit.  Input schemas (request bodies) are co-located here for
convenience when they are tightly coupled to a single endpoint.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from spendscan.llm import ReceiptPipelineResult


class OcrLineResponse(BaseModel):
    """Single OCR text line returned by the debug endpoint.

    Attributes:
        text: Recognised text content of the line.
        confidence: Recognition confidence score, 0.0-1.0.
        bbox: Bounding box as (x1, y1, x2, y2) pixel coordinates, or None.
    """

    model_config = ConfigDict(extra="forbid")
    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None


class OcrResponse(BaseModel):
    """Full OCR result returned by the /receipts/ocr debug endpoint.

    Attributes:
        text: Concatenated text from all recognised lines.
        lines: Per-line OCR results with confidence scores.
        engine: Identifier of the OCR engine used (e.g. ``"paddleocr"``).
        processing_time_ms: Wall-clock time spent on OCR in milliseconds.
        image_shape: Source image dimensions as (height, width) in pixels.
        error: Engine error message, or None on success.
    """

    model_config = ConfigDict(extra="forbid")
    text: str
    lines: list[OcrLineResponse]
    engine: str
    processing_time_ms: float
    image_shape: tuple[int, int]
    error: str | None = None


class ReadinessResponse(BaseModel):
    """Health readiness response for the /health/ready endpoint.

    Attributes:
        ready: True only when all dependency checks pass.
        checks: Per-dependency check results keyed by check name.
    """

    model_config = ConfigDict(extra="forbid")
    ready: bool
    checks: dict[str, bool]


class ReceiptAnalyzeResponse(ReceiptPipelineResult):
    """Full receipt analysis endpoint response."""


class StoredReceiptImageResponse(BaseModel):
    """Persisted receipt image page returned as part of a receipt detail response.

    Attributes:
        id: Database primary key of the image record.
        page_number: 1-based index within the multi-page receipt.
        original_filename: Client-supplied filename at upload time.
        stored_path: Legacy disk path, or empty string for DB-stored images.
        content_type: MIME type of the original upload (e.g. ``"image/png"``).
        ocr_text: Raw OCR text extracted from this page.
        ocr_engine: Identifier of the OCR engine used.
        ocr_processing_time_ms: OCR wall-clock time in milliseconds.
        image_width: Image width in pixels, or None if unknown.
        image_height: Image height in pixels, or None if unknown.
    """

    model_config = ConfigDict(extra="forbid")
    id: int
    page_number: int
    original_filename: str
    stored_path: str  # empty string "" for DB-stored images — kept for API compatibility
    content_type: str | None
    ocr_text: str
    ocr_engine: str
    ocr_processing_time_ms: float
    image_width: int | None
    image_height: int | None


class StoredReceiptItemResponse(BaseModel):
    """Single line item from a persisted receipt.

    Attributes:
        id: Database primary key of the item record.
        product_name: Name or description of the purchased product.
        quantity: Number of units purchased, or None if not parsed.
        unit_price: Price per unit, or None if not parsed.
        total_price: Total line amount (quantity x unit_price or explicit value).
        discount_amount: Discount applied to this line, or None.
        category: Inferred product category, or None.
    """

    model_config = ConfigDict(extra="forbid")
    id: int
    product_name: str
    quantity: Decimal | None
    unit_price: Decimal | None
    total_price: Decimal
    discount_amount: Decimal | None
    category: str | None


class ReceiptListItemResponse(BaseModel):
    """Summary row for a persisted receipt returned by the list endpoint.

    Attributes:
        id: Database primary key.
        status: Processing status (e.g. ``"success"``, ``"error"``).
        merchant_name: Name of the merchant, or None if not extracted.
        receipt_date: Date on the receipt, or None if not extracted.
        currency: ISO 4217 currency code (e.g. ``"PLN"``).
        total_amount: Total receipt amount.
        importance: User-assigned importance level, 0-3.
        image_count: Number of image pages attached to the receipt.
        item_count: Number of line items on the receipt.
        created_at: Timestamp when the record was persisted.
        description: Optional user note.
        folder_ids: IDs of folders this receipt belongs to.
    """

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
    """Full detail of a persisted receipt including images and line items.

    Attributes:
        id: Database primary key.
        status: Processing status (e.g. ``"success"``, ``"error"``).
        merchant_name: Name of the merchant, or None if not extracted.
        receipt_date: Date on the receipt, or None if not extracted.
        currency: ISO 4217 currency code.
        subtotal_amount: Pre-tax subtotal, or None if not extracted.
        tax_amount: Tax amount, or None if not extracted.
        total_amount: Final total amount.
        total_discount_amount: Aggregate discount applied, or None.
        payment_method: Payment method string, or None.
        description: Optional user note.
        raw_ocr_text: Full concatenated OCR output from all pages.
        warnings: Non-fatal extraction warnings produced by the pipeline.
        error: Fatal extraction error message, or None on success.
        importance: User-assigned importance level, 0-3.
        created_at: Timestamp when the record was persisted.
        images: Ordered list of receipt image pages.
        items: Parsed line items from the receipt.
    """

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
    """Editable fields of a receipt line item sent in a PATCH request.

    Attributes:
        id: Existing item primary key for updates, or None to create a new item.
        product_name: Name or description of the purchased product.
        quantity: Number of units, or None.
        unit_price: Price per unit, or None.
        total_price: Total line amount (required).
        discount_amount: Discount applied to this line, or None.
    """

    model_config = ConfigDict(extra="forbid")
    id: int | None = None
    product_name: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal
    discount_amount: Decimal | None = None


class ReceiptUpdateRequest(BaseModel):
    """Request body for PATCH /receipts/{id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        merchant_name: Override for the merchant name.
        receipt_date: Override for the receipt date.
        currency: ISO 4217 currency code override.
        total_amount: Override for the total amount.
        payment_method: Override for the payment method.
        description: User note to attach to the receipt.
        importance: Importance level 0-3, or None to leave unchanged.
        items: Replacement list of line items, or None to leave unchanged.
    """

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
