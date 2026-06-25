"""Explicit setup and status helpers for the llama.cpp runtime.

Provides ``prepare_llama_binary`` for the initial download step and
``get_llama_runtime_status`` for offline status checks without spawning
any processes or making network requests.
"""

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
    """Result of a successful llama.cpp binary preparation step.

    Attributes:
        build_tag: Resolved llama.cpp release tag that was prepared.
        binary_path: Absolute path to the ready-to-execute llama-server
            binary.
        cache_dir: Directory containing the cached binary.
    """

    build_tag: str
    binary_path: Path
    cache_dir: Path


@dataclass(frozen=True, slots=True)
class LlamaRuntimeStatus:
    """Read-only status of the configured llama.cpp runtime.

    Attributes:
        configured_build_tag: Build tag currently set in configuration,
            or ``None`` when not configured.
        cache_dir: Directory where binaries are cached.
        configured_binary_exists: Whether the binary for
            ``configured_build_tag`` is present on disk.
    """

    configured_build_tag: str | None
    cache_dir: Path
    configured_binary_exists: bool


def prepare_llama_binary(cache_dir: Path, *, build_tag: str | None = None) -> LlamaRuntimePreparation:
    """Download and cache a llama.cpp binary as an explicit setup step.

    Fetches the latest release tag from GitHub when ``build_tag`` is
    ``None``, then ensures the platform-specific binary is present in
    ``cache_dir``.

    Args:
        cache_dir: Directory used to cache downloaded binaries.
        build_tag: Specific llama.cpp release tag to prepare.  Fetches
            the latest tag from GitHub when ``None``.

    Returns:
        Preparation result describing the resolved tag and binary location.

    Raises:
        BinaryDownloadError: If the binary cannot be downloaded or extracted.
    """
    resolver = BinaryResolver(cache_dir)
    resolved_build_tag = build_tag or resolver.fetch_latest_tag()
    binary_path = resolver.ensure_binary(resolved_build_tag)
    return LlamaRuntimePreparation(build_tag=resolved_build_tag, binary_path=binary_path, cache_dir=cache_dir)


def get_llama_runtime_status(cache_dir: Path, *, build_tag: str | None) -> LlamaRuntimeStatus:
    """Return the current llama.cpp runtime status without network access.

    Checks the local filesystem only — no downloads or process spawning.

    Args:
        cache_dir: Directory where binaries are cached.
        build_tag: Build tag to check, or ``None`` when not configured.

    Returns:
        ``LlamaRuntimeStatus`` reflecting the on-disk state.
    """
    binary_name = _SERVER_BINARY_NAME.get(sys.platform, "llama-server")
    configured_binary_exists = bool(build_tag and (cache_dir / build_tag / binary_name).is_file())
    return LlamaRuntimeStatus(
        configured_build_tag=build_tag,
        cache_dir=cache_dir,
        configured_binary_exists=configured_binary_exists,
    )
