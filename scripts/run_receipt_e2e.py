"""Run the full OCR -> Gemini pipeline for local workspace receipts."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from spendscan.pipeline import ReceiptPipeline  # noqa: E402

_INPUT_DIR = _PROJECT_ROOT / "workspace" / "input"
_OUTPUT_DIR = _PROJECT_ROOT / "workspace" / "output"
_RECEIPT_PATTERN = "receipt_*.png"
_EXPECTED_RECEIPT_COUNT = 3


async def main() -> None:
    """Analyze workspace receipt PNG files and write JSON outputs."""
    receipt_paths = sorted(_INPUT_DIR.glob(_RECEIPT_PATTERN))
    if len(receipt_paths) != _EXPECTED_RECEIPT_COUNT:
        msg = f"Expected {_EXPECTED_RECEIPT_COUNT} receipt PNG files in {_INPUT_DIR}, found {len(receipt_paths)}."
        raise SystemExit(msg)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = ReceiptPipeline()
    try:
        for receipt_path in receipt_paths:
            result = await pipeline.analyze_image(receipt_path)
            output_path = _OUTPUT_DIR / f"{receipt_path.stem}.json"
            output_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
            relative_output = output_path.relative_to(_PROJECT_ROOT)
            print(f"OK {receipt_path.name} -> {relative_output} total={result.analysis.total_amount}")
    finally:
        await pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
