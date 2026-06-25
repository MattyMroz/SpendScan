"""Validation helpers for Gemini receipt JSON output.

Provides ReceiptOutputValidator, which parses raw LLM text, applies
JSON repair heuristics, validates the payload against Pydantic schemas,
deduplicates items and discounts, and appends mismatch warnings when
totals do not balance within configured tolerances.
"""

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
"""Regex that strips optional Markdown code fences from LLM JSON output."""

_TOTAL_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")
"""Maximum allowed absolute difference between summed item totals and receipt total."""

_DISCOUNT_MISMATCH_TOLERANCE: Final[Decimal] = Decimal("0.05")
"""Maximum allowed absolute difference between summed discounts and total_discount_amount."""


class ReceiptOutputValidator:
    """Parse and validate raw LLM receipt output.

    Applies a three-stage JSON repair pipeline, validates the resulting
    payload against ReceiptAnalysisResult, removes duplicate rows, and
    appends human-readable warnings for total/discount mismatches.
    """

    def validate(self, raw_text: str, *, raw_ocr_text: str) -> ReceiptAnalysisResult:
        """Parse, repair, and validate raw Gemini output into a receipt result.

        Attempts plain JSON parsing first. On failure, tries removing stray
        backslashes and then stripping all invalid escape sequences before
        giving up. Always injects raw_ocr_text into the payload so the field
        reflects exactly what was sent to the model.

        Args:
            raw_text: Raw text response from the Gemini API.
            raw_ocr_text: Original OCR transcript forwarded from the caller;
                injected verbatim into the result's raw_ocr_text field.

        Returns:
            Validated, deduplicated ReceiptAnalysisResult with any mismatch
            warnings appended.

        Raises:
            OutputValidationError: If JSON is irreparable or does not match
                the receipt schema.
        """
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
    """Compute the discount total to compare against total_discount_amount.

    Uses item-level discounts[] entries (those with item_name) when present,
    falling back to per-item discount_amount fields, then to aggregate
    discounts[] entries. This hierarchy mirrors how the LLM is instructed
    to report discounts in the system prompt.
    """
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
    """Return a copy of result with duplicate items, discounts, and warnings removed.

    Also drops aggregate discount entries that merely mirror item-level
    discounts already reported individually to avoid double-counting.
    """
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
    """Return result.items with exact duplicate rows removed, preserving order."""
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
    """Return result.discounts with exact duplicate entries removed, preserving order."""
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
    """Return values with case-insensitive duplicates removed, preserving order."""
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
    """Return a lowercased, whitespace-collapsed string for deduplication keys."""
    return " ".join(str(value or "").casefold().split())


def _extract_json(raw_text: str) -> str:
    """Extract the first JSON object from raw_text, stripping Markdown fences.

    Prefers a fenced code block if present. Falls back to slicing between
    the first ``{`` and last ``}`` in the string.
    """
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
"""Characters that may follow a backslash in a valid JSON string escape."""

_HEX_DIGITS: Final[frozenset[str]] = frozenset("0123456789abcdefABCDEF")
"""Hex digit set used to validate \\uXXXX Unicode escape sequences."""


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
