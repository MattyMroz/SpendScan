"""Render receipt OCR/LLM debug PNGs from local workspace outputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Final

from PIL import Image, ImageDraw, ImageFont

_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_DEFAULT_INPUT_DIR: Final[Path] = _PROJECT_ROOT / "workspace" / "input"
_DEFAULT_JSON_DIR: Final[Path] = _PROJECT_ROOT / "workspace" / "output"
_DEFAULT_OUTPUT_DIR: Final[Path] = _PROJECT_ROOT / "workspace" / "output" / "debug"
_DEFAULT_PATTERN: Final[str] = "receipt_*.png"
_FONT_CANDIDATES: Final[tuple[Path, ...]] = (
    Path("C:/Windows/Fonts/consola.ttf"),
    Path("C:/Windows/Fonts/DejaVuSansMono.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
)
_BOLD_FONT_CANDIDATES: Final[tuple[Path, ...]] = (
    Path("C:/Windows/Fonts/consolab.ttf"),
    Path("C:/Windows/Fonts/DejaVuSansMono-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
)


@dataclass(frozen=True, slots=True)
class DebugSection:
    """Single titled text section on the debug side."""

    title: str
    body: str


@dataclass(frozen=True, slots=True)
class RenderLayout:
    """Visual layout settings for the generated PNG."""

    padding: int = 32
    gap: int = 28
    right_panel_width: int = 980
    section_gap: int = 28
    title_gap: int = 10
    line_gap: int = 6


Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


def render_debug_png(image_path: Path, json_path: Path, output_path: Path, layout: RenderLayout) -> Path:
    """Render one receipt image and its OCR/LLM debug data to PNG."""
    pipeline_result = _load_json(json_path)
    sections = _build_sections(pipeline_result)

    with Image.open(image_path) as source_image:
        receipt_image = source_image.convert("RGB")

    regular_font = _load_font(size=18, bold=False)
    title_font = _load_font(size=24, bold=True)
    meta_font = _load_font(size=16, bold=False)

    measure_image = Image.new("RGB", (1, 1))
    measure_draw = ImageDraw.Draw(measure_image)
    text_width = layout.right_panel_width - (layout.padding * 2)
    text_height = _measure_sections(measure_draw, sections, title_font, regular_font, text_width, layout)

    canvas_width = receipt_image.width + layout.right_panel_width + (layout.padding * 2) + layout.gap
    canvas_height = max(receipt_image.height + (layout.padding * 2), text_height + (layout.padding * 2))

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    receipt_x = layout.padding
    receipt_y = layout.padding
    canvas.paste(receipt_image, (receipt_x, receipt_y))

    right_x = receipt_x + receipt_image.width + layout.gap
    draw.rectangle(
        (right_x, layout.padding, right_x + layout.right_panel_width, canvas_height - layout.padding),
        fill=(247, 248, 250),
        outline=(220, 224, 230),
    )
    _draw_meta(draw, image_path, json_path, right_x + layout.padding, layout.padding, meta_font)

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
    return output_path


def main() -> None:
    """Render all matching workspace receipts."""
    args = _parse_args()
    layout = RenderLayout(right_panel_width=args.right_width)
    image_paths = tuple(sorted(args.input_dir.glob(args.pattern)))
    if not image_paths:
        msg = f"No receipt images found in {args.input_dir} for pattern {args.pattern!r}."
        raise SystemExit(msg)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for image_path in image_paths:
        json_path = args.json_dir / f"{image_path.stem}.json"
        if not json_path.exists():
            msg = f"Missing JSON result for {image_path.name}: {json_path}"
            raise SystemExit(msg)
        output_path = args.output_dir / f"{image_path.stem}_debug.png"
        rendered_path = render_debug_png(image_path, json_path, output_path, layout)
        print(f"OK {image_path.name} -> {rendered_path.relative_to(_PROJECT_ROOT)}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render receipt OCR/LLM debug PNGs.")
    parser.add_argument("--input-dir", type=Path, default=_DEFAULT_INPUT_DIR)
    parser.add_argument("--json-dir", type=Path, default=_DEFAULT_JSON_DIR)
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pattern", default=_DEFAULT_PATTERN)
    parser.add_argument("--right-width", type=int, default=980)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"Expected JSON object in {path}"
        raise TypeError(msg)
    return data


def _build_sections(pipeline_result: dict[str, Any]) -> tuple[DebugSection, ...]:
    analysis = _as_dict(pipeline_result.get("analysis"))
    return (
        DebugSection("OCR text", str(pipeline_result.get("ocr_text", ""))),
        DebugSection("LLM JSON", json.dumps(analysis, ensure_ascii=False, indent=2)),
        DebugSection("Parsed summary", _format_summary(analysis)),
    )


def _format_summary(analysis: dict[str, Any]) -> str:
    currency = str(analysis.get("currency") or "PLN")
    lines = [
        f"Merchant: {analysis.get('merchant_name') or '-'}",
        f"Date: {analysis.get('receipt_date') or '-'}",
        f"Payment: {analysis.get('payment_method') or '-'}",
        f"Subtotal: {_money(analysis.get('subtotal_amount'), currency)}",
        f"Tax: {_money(analysis.get('tax_amount'), currency)}",
        f"Discount total: {_money(analysis.get('total_discount_amount'), currency)}",
        f"Total paid: {_money(analysis.get('total_amount'), currency)}",
    ]

    discounts = _as_dict_list(analysis.get("discounts"))
    lines.append("")
    lines.append("Discounts:")
    if discounts:
        for discount in discounts:
            description = str(discount.get("description") or "discount")
            item_name = discount.get("item_name")
            suffix = f" | item: {item_name}" if item_name else ""
            lines.append(f"- {description}: {_money(discount.get('amount'), currency)}{suffix}")
    else:
        lines.append("- none detected")

    items = _as_dict_list(analysis.get("items"))
    lines.append("")
    lines.append("Items:")
    if items:
        for item in items:
            quantity = item.get("quantity") or "-"
            unit_price = _money(item.get("unit_price"), currency)
            total_price = _money(item.get("total_price"), currency)
            discount_text = _money(item.get("discount_amount"), currency)
            item_name = item.get("name") or "-"
            lines.append(f"- {item_name} | qty {quantity} | unit {unit_price} | total {total_price}")
            if item.get("discount_amount") is not None:
                lines.append(f"  discount: {discount_text}")
    else:
        lines.append("- no items")

    warnings = analysis.get("warnings")
    lines.append("")
    lines.append("Warnings:")
    if isinstance(warnings, list) and warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")

    return "\n".join(lines)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _money(value: object, currency: str) -> str:
    if value is None:
        return "-"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return f"{value} {currency}"
    return f"{amount:.2f} {currency}"


def _load_font(*, size: int, bold: bool) -> Font:
    candidates = _BOLD_FONT_CANDIDATES if bold else _FONT_CANDIDATES
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


def _measure_sections(
    draw: ImageDraw.ImageDraw,
    sections: tuple[DebugSection, ...],
    title_font: Font,
    body_font: Font,
    width: int,
    layout: RenderLayout,
) -> int:
    total = 0
    for section in sections:
        total += _line_height(draw, title_font) + layout.title_gap
        wrapped_line_count = len(_wrap_text(draw, section.body, body_font, width))
        total += wrapped_line_count * (_line_height(draw, body_font) + layout.line_gap)
        total += layout.section_gap
    return total


def _draw_meta(
    draw: ImageDraw.ImageDraw,
    image_path: Path,
    json_path: Path,
    x_pos: int,
    y_pos: int,
    font: Font,
) -> None:
    text = f"Image: {image_path.name} | JSON: {json_path.name}"
    draw.text((x_pos, y_pos), text, fill=(70, 74, 82), font=font)


def _draw_section(
    draw: ImageDraw.ImageDraw,
    section: DebugSection,
    x_pos: int,
    y_pos: int,
    width: int,
    title_font: Font,
    body_font: Font,
    layout: RenderLayout,
) -> int:
    draw.text((x_pos, y_pos), section.title, fill=(20, 24, 32), font=title_font)
    cursor_y = y_pos + _line_height(draw, title_font) + layout.title_gap
    line_height = _line_height(draw, body_font) + layout.line_gap
    for line in _wrap_text(draw, section.body, body_font, width):
        draw.text((x_pos, cursor_y), line, fill=(34, 39, 48), font=body_font)
        cursor_y += line_height
    return cursor_y + layout.section_gap


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: Font, max_width: int) -> list[str]:
    wrapped: list[str] = []
    for raw_line in text.splitlines() or [""]:
        wrapped.extend(_wrap_line(draw, raw_line, font, max_width))
    return wrapped


def _wrap_line(draw: ImageDraw.ImageDraw, line: str, font: Font, max_width: int) -> list[str]:
    if not line:
        return [""]

    words = line.split(" ")
    wrapped: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            wrapped.append(current)
        current = _wrap_long_word(draw, word, font, max_width, wrapped)
    if current:
        wrapped.append(current)
    return wrapped


def _wrap_long_word(draw: ImageDraw.ImageDraw, word: str, font: Font, max_width: int, wrapped: list[str]) -> str:
    if _text_width(draw, word, font) <= max_width:
        return word

    current = ""
    for character in word:
        candidate = f"{current}{character}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            wrapped.append(current)
        current = character
    return current


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: Font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return round(bbox[2] - bbox[0])


def _line_height(draw: ImageDraw.ImageDraw, font: Font) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return round(bbox[3] - bbox[1])


if __name__ == "__main__":
    main()
