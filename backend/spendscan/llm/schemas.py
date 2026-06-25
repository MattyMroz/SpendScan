"""Pydantic schemas for receipt analysis.

Defines the structured data models that the LLM output is validated against:
ReceiptItem, ReceiptDiscount, ReceiptAnalysisResult, and ReceiptPipelineResult.
All monetary values are stored as Decimal to preserve precision.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReceiptItem(BaseModel):
    """Single line item extracted from a receipt.

    Attributes:
        name: Product name as printed (ASCII only per LLM rules).
        quantity: Number of units; None when not printed.
        unit_price: Price per unit; None when not printed.
        total_price: Final paid amount for this line after any discount.
        discount_amount: Per-item discount applied to this line; None if absent.
        category: Normalized product category label; None when unclassifiable.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal = Field(ge=Decimal("0"))
    discount_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    category: str | None = None


class ReceiptDiscount(BaseModel):
    """Discount entry extracted from a receipt.

    Attributes:
        description: Label as printed on the receipt (e.g. "OPUSTY LACZNIE").
        amount: Discount value as a positive decimal.
        item_name: Product name when the discount is tied to a specific item;
            None for aggregate discounts.
    """

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    amount: Decimal = Field(ge=Decimal("0"))
    item_name: str | None = None


class ReceiptAnalysisResult(BaseModel):
    """Structured receipt analysis returned by the LLM.

    Attributes:
        merchant_name: Store or merchant name; None if not visible.
        receipt_date: Transaction date; None if not visible.
        currency: ISO 4217 currency code (3 characters). Defaults to "PLN".
        subtotal_amount: Pre-tax subtotal; None if not printed.
        tax_amount: Total VAT or sales tax; None if not printed.
        total_amount: Final amount paid (required; 0 when unreadable).
        total_discount_amount: Sum of all discounts shown on receipt; None if absent.
        payment_method: Payment method label (e.g. "card", "cash"); None if absent.
        items: Ordered list of line items parsed from the receipt.
        discounts: Discount entries (aggregate or per-item).
        warnings: Human-readable notes about parsing uncertainties or mismatches.
        raw_ocr_text: Verbatim OCR transcript that was sent to the LLM.
    """

    model_config = ConfigDict(extra="forbid")

    merchant_name: str | None = None
    receipt_date: date | None = None
    currency: str = Field(default="PLN", min_length=3, max_length=3)
    subtotal_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    tax_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    total_amount: Decimal = Field(ge=Decimal("0"))
    total_discount_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    payment_method: str | None = None
    items: list[ReceiptItem] = Field(default_factory=list)
    discounts: list[ReceiptDiscount] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_ocr_text: str = ""


class ReceiptPipelineResult(BaseModel):
    """Combined OCR and LLM analysis result for an uploaded receipt.

    Attributes:
        ocr_text: Raw text produced by the OCR engine.
        ocr_engine: Identifier of the OCR engine used (e.g. "paddleocr-vl").
        ocr_processing_time_ms: OCR stage duration in milliseconds.
        analysis: Structured receipt data extracted by the LLM.
    """

    model_config = ConfigDict(extra="forbid")
    ocr_text: str
    ocr_engine: str
    ocr_processing_time_ms: float
    analysis: ReceiptAnalysisResult
