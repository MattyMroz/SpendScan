"""llama-server runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DEFAULT_SERVER_HOST: Final[str] = "127.0.0.1"
"""Local-only bind address for llama-server."""

DEFAULT_SERVER_PORT: Final[int] = 0
"""Port 0 asks the OS to choose a free port."""

DEFAULT_STARTUP_TIMEOUT_SEC: Final[float] = 120.0
"""Maximum seconds to wait for llama-server readiness."""

DEFAULT_HEALTH_TIMEOUT_SEC: Final[float] = 5.0
"""Timeout for a single llama-server health check."""

DEFAULT_GPU_LAYERS: Final[int] = -1
"""Default GPU layer offload; -1 means all layers."""

DEFAULT_CONTEXT_LENGTH: Final[int] = 4096
"""Default model context window."""


@dataclass(slots=True)
class LlamaRuntimeConfig:
    """Configuration for a managed llama-server process."""

    host: str = DEFAULT_SERVER_HOST
    port: int = DEFAULT_SERVER_PORT
    startup_timeout: float = DEFAULT_STARTUP_TIMEOUT_SEC
    health_timeout: float = DEFAULT_HEALTH_TIMEOUT_SEC
    n_gpu_layers: int = DEFAULT_GPU_LAYERS
    n_ctx: int = DEFAULT_CONTEXT_LENGTH
    flash_attn: bool = True
    verbose: bool = False
