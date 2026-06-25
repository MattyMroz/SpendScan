"""GPU memory helpers used by the OCR OOM retry logic.

Provides utilities to free CUDA caches and pick a smaller image dimension
when inference fails with an out-of-memory error.
"""

from __future__ import annotations

import contextlib
import gc
import importlib


def get_fallback_dimension(current_dim: int, fallback_sequence: tuple[int, ...]) -> int | None:
    """Return the next smaller dimension from a fallback sequence.

    Args:
        current_dim: Current longest image edge in pixels.
        fallback_sequence: Ordered sequence of candidate smaller dimensions.

    Returns:
        The first dimension in ``fallback_sequence`` that is strictly smaller
        than ``current_dim``, or ``None`` if none qualify.
    """
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
