"""Small GPU memory helpers used by OCR retry logic."""

from __future__ import annotations

import contextlib
import gc
import importlib


def get_fallback_dimension(current_dim: int, fallback_sequence: tuple[int, ...]) -> int | None:
    """Return the next smaller fallback dimension."""
    for dimension in fallback_sequence:
        if dimension < current_dim:
            return dimension
    return None


def cleanup_gpu_memory() -> None:
    """Release Python and CUDA caches when torch is installed."""
    gc.collect()
    with contextlib.suppress(ImportError, AttributeError):
        torch_module = importlib.import_module("torch")
        cuda = torch_module.cuda
        if cuda.is_available():
            cuda.empty_cache()
            with contextlib.suppress(AttributeError):
                cuda.ipc_collect()
