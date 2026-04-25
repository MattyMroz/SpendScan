"""llama.cpp runtime exports."""

from __future__ import annotations

from .binary_resolver import BinaryResolver
from .client import LlamaClient
from .config import LlamaRuntimeConfig
from .errors import BinaryDownloadError, HealthCheckError, LlamaRuntimeError, ServerStartError
from .manager import LlamaServerManager
from .setup import LlamaRuntimePreparation, LlamaRuntimeStatus, get_llama_runtime_status, prepare_llama_binary
from .types import BackendType, ChatCompletion, ChatMessage, ContentPart, PlatformInfo

__all__ = [
    "BackendType",
    "BinaryDownloadError",
    "BinaryResolver",
    "ChatCompletion",
    "ChatMessage",
    "ContentPart",
    "HealthCheckError",
    "LlamaClient",
    "LlamaRuntimeConfig",
    "LlamaRuntimeError",
    "LlamaRuntimePreparation",
    "LlamaRuntimeStatus",
    "LlamaServerManager",
    "PlatformInfo",
    "ServerStartError",
    "get_llama_runtime_status",
    "prepare_llama_binary",
]
