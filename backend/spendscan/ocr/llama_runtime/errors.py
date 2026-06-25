"""llama.cpp runtime error hierarchy.

All errors inherit from ``LlamaRuntimeError`` so callers can catch the
entire subtree with a single ``except LlamaRuntimeError``.
"""

from __future__ import annotations

from spendscan.errors import ConfigurationError, ExternalServiceError


class LlamaRuntimeError(ExternalServiceError):
    """Base error for all llama.cpp runtime failures."""


class ServerStartError(LlamaRuntimeError):
    """llama-server failed to start or did not reach a healthy state.

    Raised when the subprocess exits unexpectedly during startup or when
    the process cannot be launched at all.
    """


class HealthCheckError(LlamaRuntimeError):
    """llama-server startup health check timed out.

    Raised when the server process is running but does not return a
    healthy ``/health`` response within the configured startup timeout.
    """


class BinaryDownloadError(LlamaRuntimeError, ConfigurationError):
    """llama-server binary could not be downloaded, extracted, or resolved.

    Also inherits ``ConfigurationError`` because a missing binary is
    typically a setup or configuration issue, not a transient failure.
    """
