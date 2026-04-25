"""Pydantic schemas for receipt analysis."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReceiptItem(BaseModel):
    """Single item extracted from a receipt."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal = Field(ge=Decimal("0"))
    category: str | None = None


class ReceiptAnalysisResult(BaseModel):
    """Structured receipt analysis returned by the LLM."""

    model_config = ConfigDict(extra="forbid")

    merchant_name: str | None = None
    receipt_date: date | None = None
    currency: str = Field(default="PLN", min_length=3, max_length=3)
    subtotal_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    tax_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    total_amount: Decimal = Field(ge=Decimal("0"))
    payment_method: str | None = None
    items: list[ReceiptItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_ocr_text: str = ""


class ReceiptPipelineResult(BaseModel):
    """Combined OCR and LLM result for an uploaded receipt."""

    model_config = ConfigDict(extra="forbid")
    ocr_text: str
    ocr_engine: str
    ocr_processing_time_ms: float
    analysis: ReceiptAnalysisResult
