"""Validation helpers for Gemini receipt JSON."""

from __future__ import annotations

import json
import pathlib
import re
import time
from decimal import Decimal
from typing import Final

from loguru import logger
from pydantic import ValidationError

from spendscan.errors import OutputValidationError

from .schemas import ReceiptAnalysisResult, ReceiptDiscount, ReceiptItem

_JSON_FENCE_PATTERN: Final[re.Pattern[str]] = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_TOTAL_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")
_DISCOUNT_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")


class ReceiptOutputValidator:
    """Parse and validate raw LLM receipt output."""

    def validate(self, raw_text: str, *, raw_ocr_text: str) -> ReceiptAnalysisResult:
        """Validate raw JSON text into a receipt analysis result."""
        extracted = _extract_json(raw_text)
        try:
            payload = json.loads(extracted)
        except json.JSONDecodeError:
            try:
                payload = json.loads(_escape_stray_backslashes(extracted))
            except json.JSONDecodeError:
                stripped = re.sub(r'\\(?!["\\/bfnrtu])', "", extracted)
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    dump = pathlib.Path("workspace/output/debug") / f"gemini_bad_{int(time.time())}.txt"
                    dump.parent.mkdir(parents=True, exist_ok=True)
                    dump.write_text(extracted, encoding="utf-8")
                    logger.warning("Gemini raw output dumped to {}", dump)
                    msg = f"Gemini returned invalid JSON: {exc.msg}"
                    raise OutputValidationError(msg) from exc

        if not isinstance(payload, dict):
            msg = "Gemini JSON must be an object"
            raise OutputValidationError(msg)

        payload["raw_ocr_text"] = raw_ocr_text
        try:
            result = ReceiptAnalysisResult.model_validate(payload)
        except ValidationError as exc:
            msg = "Gemini JSON does not match receipt schema"
            raise OutputValidationError(msg) from exc

        return self._with_discount_warning(self._with_total_warning(_deduplicated_result(result)))

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


def _deduplicated_result(result: ReceiptAnalysisResult) -> ReceiptAnalysisResult:
    item_level_discounts = [discount for discount in result.discounts if discount.item_name]
    discounts = _deduplicated_discounts(result)
    if item_level_discounts and result.total_discount_amount is not None:
        discounts = [
            discount
            for discount in discounts
            if discount.item_name or abs(discount.amount - result.total_discount_amount) > _DISCOUNT_MISMATCH_TOLERANCE
        ]

    return result.model_copy(
        update={
            "items": _deduplicated_items(result),
            "discounts": discounts,
            "warnings": _deduplicated_strings(result.warnings),
        }
    )


def _deduplicated_items(result: ReceiptAnalysisResult) -> list[ReceiptItem]:
    seen: set[tuple[object, ...]] = set()
    items = []
    for item in result.items:
        key = (
            _normalized_text(item.name),
            item.quantity,
            item.unit_price,
            item.total_price,
            item.discount_amount,
            _normalized_text(item.category),
        )
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def _deduplicated_discounts(result: ReceiptAnalysisResult) -> list[ReceiptDiscount]:
    seen: set[tuple[object, ...]] = set()
    discounts = []
    for discount in result.discounts:
        key = (
            _normalized_text(discount.description),
            discount.amount,
            _normalized_text(discount.item_name),
        )
        if key in seen:
            continue
        seen.add(key)
        discounts.append(discount)
    return discounts


def _deduplicated_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for value in values:
        key = _normalized_text(value)
        if key in seen:
            continue
        seen.add(key)
        results.append(value)
    return results


def _normalized_text(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


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


_VALID_JSON_ESCAPES: Final[frozenset[str]] = frozenset('"\\/bfnrt')
_HEX_DIGITS: Final[frozenset[str]] = frozenset("0123456789abcdefABCDEF")


def _escape_stray_backslashes(text: str) -> str:
    """Double any backslash that does not start a valid JSON escape sequence."""
    out: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if char == "\\":
            nxt = text[i + 1] if i + 1 < length else ""
            if nxt in _VALID_JSON_ESCAPES or (
                nxt == "u" and i + 5 < length and all(c in _HEX_DIGITS for c in text[i + 2 : i + 6])
            ):
                out.append(char)
            else:
                out.append("\\\\")
        else:
            out.append(char)
        i += 1
    return "".join(out)
