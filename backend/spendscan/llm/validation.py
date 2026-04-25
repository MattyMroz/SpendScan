"""Validation helpers for Gemini receipt JSON."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Final

from pydantic import ValidationError

from spendscan.errors import OutputValidationError

from .schemas import ReceiptAnalysisResult

_JSON_FENCE_PATTERN: Final[re.Pattern[str]] = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_TOTAL_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")
_DISCOUNT_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")


class ReceiptOutputValidator:
    """Parse and validate raw LLM receipt output."""

    def validate(self, raw_text: str, *, raw_ocr_text: str) -> ReceiptAnalysisResult:
        """Validate raw JSON text into a receipt analysis result."""
        try:
            payload = json.loads(_extract_json(raw_text))
        except json.JSONDecodeError as exc:
            msg = f"Gemini returned invalid JSON: {exc.msg}"
            raise OutputValidationError(msg) from exc

        if not isinstance(payload, dict):
            msg = "Gemini JSON must be an object"
            raise OutputValidationError(msg)

        payload.setdefault("raw_ocr_text", raw_ocr_text)
        try:
            result = ReceiptAnalysisResult.model_validate(payload)
        except ValidationError as exc:
            msg = "Gemini JSON does not match receipt schema"
            raise OutputValidationError(msg) from exc

        return self._with_discount_warning(self._with_total_warning(result))

    def _with_total_warning(self, result: ReceiptAnalysisResult) -> ReceiptAnalysisResult:
        item_total = sum((item.total_price for item in result.items), Decimal("0"))
        if not result.items or abs(item_total - result.total_amount) <= _TOTAL_MISMATCH_TOLERANCE:
            return result

        warning = f"items total {item_total} does not match receipt total {result.total_amount}"
        return result.model_copy(update={"warnings": [*result.warnings, warning]})

    def _with_discount_warning(self, result: ReceiptAnalysisResult) -> ReceiptAnalysisResult:
        if result.total_discount_amount is None or not result.discounts:
            return result

        discount_total = _discount_total_for_comparison(result)
        if abs(discount_total - result.total_discount_amount) <= _DISCOUNT_MISMATCH_TOLERANCE:
            return result

        warning = (
            f"discounts total {discount_total} does not match receipt discount total {result.total_discount_amount}"
        )
        return result.model_copy(update={"warnings": [*result.warnings, warning]})


def _discount_total_for_comparison(result: ReceiptAnalysisResult) -> Decimal:
    item_level_discount_total = sum(
        (discount.amount for discount in result.discounts if discount.item_name),
        Decimal("0"),
    )
    if item_level_discount_total > Decimal("0"):
        return item_level_discount_total

    item_field_discount_total = sum(
        (item.discount_amount for item in result.items if item.discount_amount is not None),
        Decimal("0"),
    )
    if item_field_discount_total > Decimal("0"):
        return item_field_discount_total

    return sum((discount.amount for discount in result.discounts), Decimal("0"))


def _extract_json(raw_text: str) -> str:
    text = raw_text.strip()
    fence_match = _JSON_FENCE_PATTERN.search(text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]
