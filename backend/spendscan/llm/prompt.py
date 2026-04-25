"""Gemini prompt for receipt parsing."""

from __future__ import annotations

from typing import Final

SYSTEM_PROMPT: Final[str] = """
You extract structured data from Polish retail receipts.
Return only valid JSON matching this schema:
{
  "merchant_name": string | null,
  "receipt_date": "YYYY-MM-DD" | null,
  "currency": "PLN",
  "subtotal_amount": decimal string | null,
  "tax_amount": decimal string | null,
  "total_amount": decimal string,
  "payment_method": string | null,
  "items": [
    {
      "name": string,
      "quantity": decimal string | null,
      "unit_price": decimal string | null,
      "total_price": decimal string,
      "category": string | null
    }
  ],
  "warnings": [string],
  "raw_ocr_text": string
}
Use decimal strings with dot separator. Do not invent missing values; use null.
""".strip()


def build_receipt_prompt(ocr_text: str) -> str:
    """Build user prompt for receipt JSON extraction."""
    return f"Extract receipt JSON from this OCR text:\n\n{ocr_text.strip()}"
