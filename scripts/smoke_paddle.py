"""Smoke test PaddleOCR + Gemini na realnych paragonach z timingiem per faza."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from spendscan.llm import GeminiReceiptClient  # noqa: E402
from spendscan.ocr import OcrService  # noqa: E402

_INPUT_DIR = _PROJECT_ROOT / "workspace" / "input" / "paired_receipts"
_OUTPUT_DIR = _PROJECT_ROOT / "workspace" / "output"


def _discover_receipts() -> list[list[Path]]:
    """Group paired receipt PNGs by stem prefix (receipt_NNN_*)."""
    groups: dict[str, list[Path]] = {}
    for path in sorted(_INPUT_DIR.glob("receipt_*.png")):
        key = path.stem.rsplit("_", 1)[0]
        groups.setdefault(key, []).append(path)
    return [sorted(pages) for _, pages in sorted(groups.items())]


async def main() -> None:  # noqa: PLR0915
    receipt_groups = _discover_receipts()
    if not receipt_groups:
        raise SystemExit(f"No receipts in {_INPUT_DIR}")

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    smoke_dir = _OUTPUT_DIR / "smoke"
    if smoke_dir.exists():
        for old in smoke_dir.iterdir():
            old.unlink()
    smoke_dir.mkdir(parents=True, exist_ok=True)
    report_path = smoke_dir / "_report.json"
    summary_md = smoke_dir / "_SUMMARY.md"

    ocr = OcrService()
    llm = GeminiReceiptClient()

    print("== Preloading PaddleOCR-VL ==")
    preload_start = time.perf_counter()
    await ocr.initialize()
    preload_s = time.perf_counter() - preload_start
    print(f"OCR ready in {preload_s:.1f}s\n")

    results: list[dict[str, object]] = []
    try:
        for group in receipt_groups:
            name = group[0].stem.rsplit("_", 1)[0]
            print(f"-- {name} ({len(group)} page(s)) --")

            ocr_pages: list[dict[str, object]] = []
            ocr_total_s = 0.0
            combined_text_parts: list[str] = []
            for idx, page in enumerate(group, start=1):
                t0 = time.perf_counter()
                ocr_result = await ocr.recognize(page)
                elapsed = time.perf_counter() - t0
                ocr_total_s += elapsed
                page_text = (ocr_result.text or "").strip()
                if len(group) > 1:
                    combined_text_parts.append(f"--- PAGE {idx}: {page.name} ---\n{page_text}")
                else:
                    combined_text_parts.append(page_text)
                ocr_pages.append(
                    {
                        "page": idx,
                        "file": page.name,
                        "ocr_time_s": round(elapsed, 2),
                        "chars": len(page_text),
                        "lines": len(ocr_result.lines or []),
                        "error": ocr_result.error,
                    }
                )
                print(f"  page {idx} OCR: {elapsed:.2f}s  chars={len(page_text)}  err={ocr_result.error}")

            combined_text = "\n\n".join(combined_text_parts).strip()
            (smoke_dir / f"{name}_ocr.txt").write_text(combined_text + "\n", encoding="utf-8")

            t1 = time.perf_counter()
            analysis_dump: dict[str, object] | None = None
            try:
                analysis = await llm.analyze_receipt(ocr_text=combined_text, image_paths=tuple(group))
                llm_s = time.perf_counter() - t1
                analysis_dump = analysis.model_dump(mode="json")
                items_count = len(analysis.items)
                total = float(analysis.total_amount) if analysis.total_amount is not None else None
                merchant = analysis.merchant_name
                err = None
            except Exception as exc:  # noqa: BLE001
                llm_s = time.perf_counter() - t1
                items_count = 0
                total = None
                merchant = None
                err = f"{type(exc).__name__}: {exc}"
            print(f"  Gemini: {llm_s:.2f}s  items={items_count}  total={total}  merchant={merchant}  err={err}")

            if analysis_dump is not None:
                (smoke_dir / f"{name}_analysis.json").write_text(
                    json.dumps(analysis_dump, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

            results.append(
                {
                    "receipt": name,
                    "pages": ocr_pages,
                    "ocr_total_s": round(ocr_total_s, 2),
                    "gemini_s": round(llm_s, 2),
                    "total_s": round(ocr_total_s + llm_s, 2),
                    "items": items_count,
                    "total_amount": total,
                    "merchant": merchant,
                    "gemini_error": err,
                }
            )

        avg_ocr = sum(r["ocr_total_s"] for r in results) / len(results)  # type: ignore[arg-type]
        avg_llm = sum(r["gemini_s"] for r in results) / len(results)  # type: ignore[arg-type]
        avg_total = sum(r["total_s"] for r in results) / len(results)  # type: ignore[arg-type]

        report = {
            "preload_s": round(preload_s, 1),
            "receipts": results,
            "averages": {
                "ocr_s": round(avg_ocr, 2),
                "gemini_s": round(avg_llm, 2),
                "total_s": round(avg_total, 2),
            },
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        md_lines = [
            "# Smoke test PaddleOCR-VL + Gemini",
            "",
            f"- Preload: **{preload_s:.1f}s**",
            f"- Avg OCR: **{avg_ocr:.2f}s/paragon**",
            f"- Avg Gemini: **{avg_llm:.2f}s/paragon**",
            f"- Avg Total: **{avg_total:.2f}s/paragon**",
            "",
            "| Paragon | Stron | OCR (s) | Gemini (s) | Items | Total | Sklep |",
            "|---|---|---|---|---|---|---|",
        ]
        md_lines.extend(
            f"| {r['receipt']} | {len(r['pages'])} | {r['ocr_total_s']} | {r['gemini_s']} | "  # type: ignore[arg-type]
            f"{r['items']} | {r['total_amount']} | {r['merchant']} |"
            for r in results
        )
        summary_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

        print(f"\n== Avg OCR={avg_ocr:.2f}s  Gemini={avg_llm:.2f}s  Total={avg_total:.2f}s ==")
        print(f"Report: {report_path.relative_to(_PROJECT_ROOT)}")
        print(f"Summary: {summary_md.relative_to(_PROJECT_ROOT)}")
    finally:
        print("\nCleaning up OCR...")
        await ocr.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
