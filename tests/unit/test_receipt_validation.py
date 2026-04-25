from __future__ import annotations

from decimal import Decimal

import pytest

from spendscan.errors import OutputValidationError
from spendscan.llm.validation import ReceiptOutputValidator


def test_receipt_output_validator_accepts_fenced_json() -> None:
    result = ReceiptOutputValidator().validate(
        """
        ```json
        {
          "merchant_name": "TEST SHOP",
          "currency": "PLN",
          "total_amount": "12.50",
                    "total_discount_amount": "1.00",
                    "items": [{"name": "Milk", "total_price": "12.50", "discount_amount": "1.00"}],
                    "discounts": [{"description": "OPUST", "amount": "1.00", "item_name": "Milk"}],
          "warnings": []
        }
        ```
        """,
        raw_ocr_text="TOTAL 12.50",
    )

    assert result.merchant_name == "TEST SHOP"
    assert result.total_discount_amount == Decimal("1.00")
    assert result.items[0].discount_amount == Decimal("1.00")
    assert result.discounts[0].amount == Decimal("1.00")
    assert result.raw_ocr_text == "TOTAL 12.50"


def test_receipt_output_validator_adds_total_mismatch_warning() -> None:
    result = ReceiptOutputValidator().validate(
        """
        {
          "currency": "PLN",
          "total_amount": "10.00",
          "items": [{"name": "Milk", "total_price": "8.00"}],
          "warnings": []
        }
        """,
        raw_ocr_text="TOTAL 10.00",
    )

    assert result.warnings == ["items total 8.00 does not match receipt total 10.00"]


def test_receipt_output_validator_rejects_invalid_json() -> None:
    validator = ReceiptOutputValidator()

    with pytest.raises(OutputValidationError, match="invalid JSON"):
        validator.validate("not-json", raw_ocr_text="")


def test_receipt_output_validator_adds_discount_mismatch_warning() -> None:
    result = ReceiptOutputValidator().validate(
        """
                {
                    "currency": "PLN",
                    "total_amount": "10.00",
                    "total_discount_amount": "3.00",
                    "items": [{"name": "Milk", "total_price": "10.00"}],
                    "discounts": [{"description": "OPUST", "amount": "2.00"}],
                    "warnings": []
                }
                """,
        raw_ocr_text="TOTAL 10.00",
    )

    assert result.warnings == ["discounts total 2.00 does not match receipt discount total 3.00"]


def test_receipt_output_validator_ignores_aggregate_discount_duplicate() -> None:
    result = ReceiptOutputValidator().validate(
        """
                {
                    "currency": "PLN",
                    "total_amount": "3.22",
                    "total_discount_amount": "64.32",
                    "items": [
                        {"name": "Mielone", "total_price": "1.12", "discount_amount": "21.96"},
                        {"name": "Pomidor", "total_price": "1.30", "discount_amount": "28.92"},
                        {"name": "Rzodkiewka", "total_price": "0.58", "discount_amount": "11.38"},
                        {"name": "Bułka", "total_price": "0.22", "discount_amount": "2.06"}
                    ],
                    "discounts": [
                        {"description": "OPUST", "amount": "21.96", "item_name": "Mielone"},
                        {"description": "OPUST", "amount": "28.92", "item_name": "Pomidor"},
                        {"description": "OPUST", "amount": "11.38", "item_name": "Rzodkiewka"},
                        {"description": "OPUST", "amount": "2.06", "item_name": "Bułka"},
                        {"description": "OPUSTY ŁĄCZNIE", "amount": "64.32", "item_name": null}
                    ],
                    "warnings": []
                }
                """,
        raw_ocr_text="OPUSTY ŁĄCZNIE -64,32",
    )

    assert result.warnings == []
