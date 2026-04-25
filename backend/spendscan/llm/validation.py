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

        return self._with_total_warning(result)

    def _with_total_warning(self, result: ReceiptAnalysisResult) -> ReceiptAnalysisResult:
        item_total = sum((item.total_price for item in result.items), Decimal("0"))
        if not result.items or abs(item_total - result.total_amount) <= _TOTAL_MISMATCH_TOLERANCE:
            return result

        warning = f"items total {item_total} does not match receipt total {result.total_amount}"
        return result.model_copy(update={"warnings": [*result.warnings, warning]})


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
