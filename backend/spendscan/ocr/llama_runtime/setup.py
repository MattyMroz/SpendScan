"""Explicit setup/status helpers for llama.cpp runtime."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .binary_resolver import BinaryResolver

_SERVER_BINARY_NAME: dict[str, str] = {
    "win32": "llama-server.exe",
    "linux": "llama-server",
    "darwin": "llama-server",
}


@dataclass(frozen=True, slots=True)
class LlamaRuntimePreparation:
    """Result of a deliberate llama.cpp binary preparation."""

    build_tag: str
    binary_path: Path
    cache_dir: Path


@dataclass(frozen=True, slots=True)
class LlamaRuntimeStatus:
    """Read-only status of configured llama.cpp runtime."""

    configured_build_tag: str | None
    cache_dir: Path
    configured_binary_exists: bool


def prepare_llama_binary(cache_dir: Path, *, build_tag: str | None = None) -> LlamaRuntimePreparation:
    """Download/cache a concrete llama.cpp build as a setup step."""
    resolver = BinaryResolver(cache_dir)
    resolved_build_tag = build_tag or resolver.fetch_latest_tag()
    binary_path = resolver.ensure_binary(resolved_build_tag)
    return LlamaRuntimePreparation(build_tag=resolved_build_tag, binary_path=binary_path, cache_dir=cache_dir)


def get_llama_runtime_status(cache_dir: Path, *, build_tag: str | None) -> LlamaRuntimeStatus:
    """Return runtime status without network access."""
    binary_name = _SERVER_BINARY_NAME.get(sys.platform, "llama-server")
    configured_binary_exists = bool(build_tag and (cache_dir / build_tag / binary_name).is_file())
    return LlamaRuntimeStatus(
        configured_build_tag=build_tag,
        cache_dir=cache_dir,
        configured_binary_exists=configured_binary_exists,
    )
