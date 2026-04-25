from __future__ import annotations

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
          "items": [{"name": "Milk", "total_price": "12.50"}],
          "warnings": []
        }
        ```
        """,
        raw_ocr_text="TOTAL 12.50",
    )

    assert result.merchant_name == "TEST SHOP"
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
