"""OCR output cleaning utilities."""

from __future__ import annotations

import re
from typing import Final

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


def parse_ocr_output(raw_text: str) -> tuple[str, list[str]]:
    """Clean OCR output and split it into non-empty lines."""
    cleaned = _SPECIAL_TOKEN_PATTERN.sub("", raw_text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    return "\n".join(lines), lines
