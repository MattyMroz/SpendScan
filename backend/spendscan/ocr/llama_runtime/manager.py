"""Managed llama-server subprocess lifecycle."""

from __future__ import annotations

import atexit
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Final

from loguru import logger

from .binary_resolver import BinaryResolver
from .client import LlamaClient
from .config import LlamaRuntimeConfig
from .errors import HealthCheckError, ServerStartError

_HEALTH_POLL_INTERVAL_SEC: Final[float] = 0.5


class LlamaServerManager:
    """Start, health-check, and stop a llama-server subprocess."""

    __slots__ = ("_binary_resolver", "_client", "_port", "_process", "config")

    def __init__(
        self,
        config: LlamaRuntimeConfig | None = None,
        *,
        binary_resolver: BinaryResolver | None = None,
    ) -> None:
        self.config = config or LlamaRuntimeConfig()
        self._binary_resolver = binary_resolver or BinaryResolver()
        self._process: subprocess.Popen[str] | None = None
        self._client: LlamaClient | None = None
        self._port = 0

    @property
    def is_running(self) -> bool:
        """Return whether the server process is alive."""
        return self._process is not None and self._process.poll() is None

    @property
    def port(self) -> int:
        """Return bound server port."""
        return self._port

    @property
    def client(self) -> LlamaClient:
        """Return connected HTTP client."""
        if self._client is None:
            msg = "Server not started; call start() first"
            raise ServerStartError(msg)
        return self._client

    def start(self, model_path: str | Path, *, mmproj_path: str | Path, build_tag: str) -> LlamaClient:
        """Start llama-server using a prepared cached binary."""
        if self.is_running:
            return self.client

        binary_path = self._binary_resolver.resolve_cached_binary(build_tag)
        self._port = self._resolve_port()
        command = self._build_command(binary_path, Path(model_path), Path(mmproj_path))

        try:
            self._process = subprocess.Popen(  # noqa: S603
                command,
                stdout=subprocess.PIPE if not self.config.verbose else None,
                stderr=subprocess.PIPE if not self.config.verbose else None,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except OSError as exc:
            msg = f"Failed to start llama-server: {exc}"
            raise ServerStartError(msg) from exc

        atexit.register(self.stop)
        self._client = LlamaClient(f"http://{self.config.host}:{self._port}", timeout=120.0)
        self._wait_for_healthy()
        logger.info("llama-server ready on port {}", self._port)
        return self._client

    def stop(self) -> None:
        """Stop llama-server if it is running."""
        if self._process is None:
            return

        if self._client is not None:
            self._client.close()
            self._client = None

        try:
            self._process.terminate()
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)
        except OSError:
            logger.warning("Failed to stop llama-server cleanly")
        finally:
            self._process = None
            self._port = 0

    @contextmanager
    def serve(self, model_path: str | Path, *, mmproj_path: str | Path, build_tag: str) -> Generator[LlamaClient]:
        """Start a server for a context manager scope."""
        client = self.start(model_path, mmproj_path=mmproj_path, build_tag=build_tag)
        try:
            yield client
        finally:
            self.stop()

    def _resolve_port(self) -> int:
        if self.config.port != 0:
            return self.config.port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", 0))
            return int(sock.getsockname()[1])

    def _build_command(self, binary: Path, model_path: Path, mmproj_path: Path) -> list[str]:
        command = [
            str(binary),
            "--model",
            str(model_path),
            "--mmproj",
            str(mmproj_path),
            "--host",
            self.config.host,
            "--port",
            str(self._port),
            "--n-gpu-layers",
            str(self.config.n_gpu_layers),
            "--ctx-size",
            str(self.config.n_ctx),
        ]
        if self.config.flash_attn:
            command.extend(["--flash-attn", "on"])
        return command

    def _wait_for_healthy(self) -> None:
        if self._client is None or self._process is None:
            msg = "No llama-server process to health-check"
            raise ServerStartError(msg)

        deadline = time.monotonic() + self.config.startup_timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                stderr_text = self._process.stderr.read() if self._process.stderr else ""
                msg = f"llama-server exited during startup (code {self._process.returncode})"
                if stderr_text:
                    msg = f"{msg}: {stderr_text[:500]}"
                self._process = None
                raise ServerStartError(msg)
            if self._client.health(timeout=self.config.health_timeout):
                return
            time.sleep(_HEALTH_POLL_INTERVAL_SEC)

        msg = f"llama-server health check timed out after {self.config.startup_timeout}s"
        raise HealthCheckError(msg)
