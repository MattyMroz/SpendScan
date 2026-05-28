"""OCR output cleaning utilities."""

from __future__ import annotations

import re
from typing import Final

_REPEAT_MIN_TOTAL_CHARS: Final[int] = 12
_REPEAT_MAX_UNIT_CHARS: Final[int] = 12
_REPEAT_MIN_REPETITIONS: Final[int] = 4

_SPECIAL_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"<\|endoftext\|>"
    r"|<\|end\|>"
    r"|<\|assistant\|>"
    r"|<\|user\|>"
    r"|<\|system\|>"
    r"|<\|observation\|>"
    r"|<\|im_end\|>"
    r"|<pad>"
    r"|</s>"
    r"|<s>"
    r"|<eos>",
    flags=re.IGNORECASE,
)


def trim_repeated_ocr_suffix(text: str) -> str:
    """Trim degenerate repeated tail from PaddleOCR-VL output."""
    chars = [(i, c) for i, c in enumerate(text) if not c.isspace()]
    n = len(chars)
    if n < _REPEAT_MIN_TOTAL_CHARS:
        return text
    max_unit = min(_REPEAT_MAX_UNIT_CHARS, n // _REPEAT_MIN_REPETITIONS)
    for unit_length in range(1, max_unit + 1):
        unit = [c for _, c in chars[n - unit_length : n]]
        repetitions = 1
        while n >= unit_length * (repetitions + 1):
            start = n - unit_length * (repetitions + 1)
            end = start + unit_length
            if [c for _, c in chars[start:end]] == unit:
                repetitions += 1
            else:
                break
        repeated_chars = repetitions * unit_length
        if repetitions >= _REPEAT_MIN_REPETITIONS and repeated_chars >= _REPEAT_MIN_TOTAL_CHARS:
            return text[: chars[n - repeated_chars][0]]
    return text


def parse_ocr_output(raw_text: str) -> tuple[str, list[str]]:
    """Clean OCR output and split it into non-empty lines."""
    cleaned = _SPECIAL_TOKEN_PATTERN.sub("", raw_text)
    cleaned = trim_repeated_ocr_suffix(cleaned)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    return "\n".join(lines), lines
