"""Prepare Qianfan OCR files and llama.cpp runtime for local testing."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from spendscan.config import get_settings  # noqa: E402
from spendscan.ocr.llama_runtime import prepare_llama_binary  # noqa: E402
from spendscan.ocr.qianfan import QianfanModelResolver  # noqa: E402

_ENV_FILE = _PROJECT_ROOT / ".env"


def main() -> None:
    """Download required OCR model files and a concrete llama.cpp build."""
    settings = get_settings()
    QianfanModelResolver(settings.resolved_qianfan_model_dir).ensure_files()
    preparation = prepare_llama_binary(
        settings.resolved_llama_cache_dir,
        build_tag=settings.llama_build_tag,
    )
    _upsert_env_value("SPENDSCAN_LLAMA_BUILD_TAG", preparation.build_tag)
    print(f"Prepared llama.cpp build: {preparation.build_tag}")
    print(f"Binary: {preparation.binary_path}")


def _upsert_env_value(name: str, value: str) -> None:
    lines = _ENV_FILE.read_text(encoding="utf-8").splitlines() if _ENV_FILE.exists() else []
    prefix = f"{name}="
    replaced = False
    next_lines: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            next_lines.append(f"{name}={value}")
            replaced = True
        else:
            next_lines.append(line)
    if not replaced:
        next_lines.append(f"{name}={value}")
    _ENV_FILE.write_text("\n".join(next_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
