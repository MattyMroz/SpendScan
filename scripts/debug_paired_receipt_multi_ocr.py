"""Render debug PNGs for paired multi-image receipt OCR checks."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from PIL import Image, ImageDraw
from render_receipt_debug import (
    DebugSection,
    RenderLayout,
    _draw_section,
    _line_height,
    _load_font,
    _measure_sections,
)

_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_BACKEND_DIR: Final[Path] = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

if TYPE_CHECKING:
    from spendscan.pipeline import ReceiptImagePipelineResult, ReceiptPipeline

_DEFAULT_INPUT_DIR: Final[Path] = _PROJECT_ROOT / "workspace" / "input" / "paired_receipts"
_DEFAULT_OUTPUT_DIR: Final[Path] = _PROJECT_ROOT / "workspace" / "output" / "debug"
_PAGE_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r"^(?P<group>.+)_(?P<page>\d+)\.png$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ReceiptPageGroup:
    """One logical receipt made of multiple page images."""

    name: str
    image_paths: tuple[Path, ...]


def main() -> None:
    """Run async debug rendering."""
    asyncio.run(_main())


async def _main() -> None:
    args = _parse_args()
    groups = _find_page_groups(args.input_dir)
    if not groups:
        msg = f"No paired receipt PNGs found in {args.input_dir}."
        raise SystemExit(msg)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    from spendscan.pipeline import ReceiptPipeline

    pipeline = ReceiptPipeline()
    try:
        for group in groups:
            if not args.ocr_only:
                result = await pipeline.analyze_images(group.image_paths)
                pages = result.images
                json_path = args.output_dir / f"{group.name}_multi_analysis.json"
                json_path.write_text(result.receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
                analysis = result.receipt.analysis.model_dump(mode="json")
            else:
                pages = await _recognize_pages(pipeline, group.image_paths)
                analysis = None

            output_path = args.output_dir / f"{group.name}_multi_ocr_debug.png"
            _render_group_debug_png(
                group=group,
                pages=pages,
                analysis=analysis,
                output_path=output_path,
                max_image_width=args.max_image_width,
                right_width=args.right_width,
            )
            relative_output = output_path.relative_to(_PROJECT_ROOT)
            print(f"OK {group.name}: {len(group.image_paths)} pages -> {relative_output}")
    finally:
        await pipeline.cleanup()


async def _recognize_pages(
    pipeline: ReceiptPipeline,
    image_paths: tuple[Path, ...],
) -> tuple[ReceiptImagePipelineResult, ...]:
    """Run OCR for each page and keep page metadata for rendering."""
    from spendscan.pipeline import ReceiptImagePipelineResult

    page_results: list[ReceiptImagePipelineResult] = []
    for index, image_path in enumerate(image_paths, start=1):
        page_results.append(
            ReceiptImagePipelineResult(
                image_path=image_path,
                page_number=index,
                ocr=await pipeline.recognize_image(image_path),
            )
        )
    return tuple(page_results)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render OCR debug PNGs for paired receipt page images.")
    parser.add_argument("--input-dir", type=Path, default=_DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR)
    parser.add_argument("--right-width", type=int, default=980)
    parser.add_argument("--max-image-width", type=int, default=760)
    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="Run OCR only. By default the script runs the full multi-image OCR -> LLM pipeline.",
    )
    return parser.parse_args()


def _find_page_groups(input_dir: Path) -> tuple[ReceiptPageGroup, ...]:
    grouped_paths: dict[str, dict[int, Path]] = {}
    for image_path in sorted(input_dir.glob("*.png")):
        match = _PAGE_SUFFIX_RE.match(image_path.name)
        if match is None:
            continue
        group_name = match.group("group")
        page_number = int(match.group("page"))
        grouped_paths.setdefault(group_name, {})[page_number] = image_path

    groups: list[ReceiptPageGroup] = []
    for group_name, pages in sorted(grouped_paths.items()):
        if len(pages) < 2:
            continue
        groups.append(ReceiptPageGroup(name=group_name, image_paths=tuple(path for _, path in sorted(pages.items()))))
    return tuple(groups)


def _render_group_debug_png(
    *,
    group: ReceiptPageGroup,
    pages: tuple[ReceiptImagePipelineResult, ...],
    analysis: dict[str, Any] | None,
    output_path: Path,
    max_image_width: int,
    right_width: int,
) -> None:
    layout = RenderLayout(right_panel_width=right_width)
    page_strip = _build_page_strip(pages, max_image_width=max_image_width)
    sections = _build_sections(group, pages, analysis)

    regular_font = _load_font(size=18, bold=False)
    title_font = _load_font(size=24, bold=True)
    meta_font = _load_font(size=16, bold=False)

    measure_image = Image.new("RGB", (1, 1))
    measure_draw = ImageDraw.Draw(measure_image)
    text_width = right_width - (layout.padding * 2)
    text_height = _measure_sections(measure_draw, sections, title_font, regular_font, text_width, layout)

    canvas_width = page_strip.width + right_width + (layout.padding * 2) + layout.gap
    canvas_height = max(page_strip.height + (layout.padding * 2), text_height + (layout.padding * 2))

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    canvas.paste(page_strip, (layout.padding, layout.padding))

    right_x = layout.padding + page_strip.width + layout.gap
    draw.rectangle(
        (right_x, layout.padding, right_x + right_width, canvas_height - layout.padding),
        fill=(247, 248, 250),
        outline=(220, 224, 230),
    )

    draw.text(
        (right_x + layout.padding, layout.padding),
        f"Multi OCR group: {group.name} | pages: {len(pages)}",
        fill=(70, 74, 82),
        font=meta_font,
    )
    cursor_y = layout.padding + _line_height(measure_draw, meta_font) + layout.section_gap
    for section in sections:
        cursor_y = _draw_section(
            draw,
            section,
            right_x + layout.padding,
            cursor_y,
            text_width,
            title_font,
            regular_font,
            layout,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def _build_page_strip(pages: tuple[ReceiptImagePipelineResult, ...], *, max_image_width: int) -> Image.Image:
    label_font = _load_font(size=20, bold=True)
    measure_image = Image.new("RGB", (1, 1))
    measure_draw = ImageDraw.Draw(measure_image)
    label_height = _line_height(measure_draw, label_font) + 16
    gap = 24
    padding = 20

    scaled_pages: list[tuple[str, Image.Image]] = []
    for page in pages:
        with Image.open(page.image_path) as source_image:
            image = source_image.convert("RGB")
        ratio = min(1.0, max_image_width / image.width)
        scaled_size = (round(image.width * ratio), round(image.height * ratio))
        scaled_pages.append((f"Page {page.page_number}: {page.image_path.name}", image.resize(scaled_size)))

    strip_width = max(image.width for _, image in scaled_pages) + (padding * 2)
    strip_height = sum(label_height + image.height for _, image in scaled_pages) + gap * (len(scaled_pages) - 1)
    strip_height += padding * 2

    strip = Image.new("RGB", (strip_width, strip_height), "white")
    draw = ImageDraw.Draw(strip)
    cursor_y = padding
    for label, image in scaled_pages:
        draw.text((padding, cursor_y), label, fill=(20, 24, 32), font=label_font)
        cursor_y += label_height
        strip.paste(image, (padding, cursor_y))
        cursor_y += image.height + gap
    return strip


def _build_sections(
    group: ReceiptPageGroup,
    pages: tuple[ReceiptImagePipelineResult, ...],
    analysis: dict[str, Any] | None,
) -> tuple[DebugSection, ...]:
    sections = [
        DebugSection("Page OCR status", _format_page_status(pages)),
        DebugSection("Combined OCR text", _format_combined_ocr_text(pages)),
    ]
    if analysis is not None:
        sections.append(DebugSection("LLM analysis JSON", json.dumps(analysis, ensure_ascii=False, indent=2)))
    sections.append(DebugSection("Input files", "\n".join(path.name for path in group.image_paths)))
    return tuple(sections)


def _format_page_status(pages: tuple[ReceiptImagePipelineResult, ...]) -> str:
    lines: list[str] = []
    for page in pages:
        status = "OK" if page.ocr.error is None else f"ERROR: {page.ocr.error}"
        lines.append(
            f"page {page.page_number}: {page.image_path.name} | "
            f"engine={page.ocr.engine or '-'} | lines={page.ocr.line_count} | "
            f"time={page.ocr.processing_time_ms:.0f} ms | {status}"
        )
    return "\n".join(lines)


def _format_combined_ocr_text(pages: tuple[ReceiptImagePipelineResult, ...]) -> str:
    if len(pages) == 1:
        return pages[0].ocr.text
    return "\n\n".join(
        f"--- PAGE {page.page_number}: {page.image_path.name} ---\n{page.ocr.text.strip()}" for page in pages
    ).strip()


if __name__ == "__main__":
    main()
