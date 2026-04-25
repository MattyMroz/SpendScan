"""llama.cpp runtime errors."""

from __future__ import annotations

from spendscan.errors import ConfigurationError, ExternalServiceError


class LlamaRuntimeError(ExternalServiceError):
    """Base error for llama.cpp runtime operations."""


class ServerStartError(LlamaRuntimeError):
    """llama-server failed to start or reach a healthy state."""


class HealthCheckError(LlamaRuntimeError):
    """llama-server health check failed."""


class BinaryDownloadError(LlamaRuntimeError, ConfigurationError):
    """llama-server binary could not be downloaded or resolved."""
