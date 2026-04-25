"""Platform detection and llama-server binary preparation."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Final

import httpx
from loguru import logger

from spendscan.config import project_root

from .errors import BinaryDownloadError
from .types import BackendType, PlatformInfo

_RELEASES_API: Final[str] = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
_RELEASE_DOWNLOAD_BASE: Final[str] = "https://github.com/ggml-org/llama.cpp/releases/download"
_DEFAULT_CACHE_DIR: Final[Path] = Path("external/bin/llama")
_DOWNLOAD_CHUNK_BYTES: Final[int] = 1024 * 1024
_SERVER_BINARY_NAME: Final[dict[str, str]] = {
    "win32": "llama-server.exe",
    "linux": "llama-server",
    "darwin": "llama-server",
}


def _asset_name(build_tag: str, os_name: str, arch: str, backend: BackendType) -> str:
    """Return upstream llama.cpp release asset name."""
    if os_name == "win32":
        arch_name = "x64" if arch == "x86_64" else arch
        if backend == BackendType.CUDA:
            return f"llama-{build_tag}-bin-win-cuda-12.4-x64.zip"
        if backend == BackendType.VULKAN:
            return f"llama-{build_tag}-bin-win-vulkan-{arch_name}.zip"
        return f"llama-{build_tag}-bin-win-cpu-{arch_name}.zip"

    if os_name == "linux":
        if backend == BackendType.VULKAN:
            return f"llama-{build_tag}-bin-ubuntu-vulkan-x64.tar.gz"
        return f"llama-{build_tag}-bin-ubuntu-x64.tar.gz"

    if os_name == "darwin":
        arch_name = "arm64" if arch in {"arm64", "aarch64"} else "x64"
        return f"llama-{build_tag}-bin-macos-{arch_name}.tar.gz"

    msg = f"Unsupported platform: {os_name}/{arch}"
    raise BinaryDownloadError(msg)


class BinaryResolver:
    """Resolve, download, and cache llama-server binaries."""

    __slots__ = ("cache_dir",)

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or project_root() / _DEFAULT_CACHE_DIR

    def fetch_latest_tag(self) -> str:
        """Fetch latest llama.cpp release tag from GitHub."""
        try:
            response = httpx.get(
                _RELEASES_API,
                headers={"Accept": "application/vnd.github+json"},
                timeout=30.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            tag = response.json().get("tag_name", "")
        except httpx.HTTPError as exc:
            msg = f"Failed to fetch latest llama.cpp release tag: {exc}"
            raise BinaryDownloadError(msg) from exc

        if not isinstance(tag, str) or not tag:
            msg = "No tag_name in llama.cpp release response"
            raise BinaryDownloadError(msg)
        return tag

    def ensure_binary(self, build_tag: str) -> Path:
        """Download a specific llama-server build when missing."""
        binary_path = self._binary_path(build_tag)
        if binary_path.exists():
            return binary_path

        platform_info = self.detect_platform()
        self._download_and_extract(build_tag, platform_info)

        if not binary_path.exists():
            msg = f"llama-server not found after extraction: {binary_path}"
            raise BinaryDownloadError(msg)
        if sys.platform != "win32":
            binary_path.chmod(binary_path.stat().st_mode | 0o755)
        return binary_path

    def resolve_cached_binary(self, build_tag: str) -> Path:
        """Resolve a prepared llama-server binary without network access."""
        binary_path = self._binary_path(build_tag)
        if binary_path.exists():
            return binary_path
        msg = f"Configured llama.cpp build {build_tag!r} is missing at {binary_path}. Run OCR setup first."
        raise BinaryDownloadError(msg)

    def detect_platform(self) -> PlatformInfo:
        """Detect current platform and preferred llama.cpp backend."""
        os_name = sys.platform
        arch = platform.machine().lower()
        if arch in {"amd64", "x86_64"}:
            arch = "x86_64"
        elif arch in {"arm64", "aarch64"}:
            arch = "arm64"
        backend, cuda_version = self._select_backend()
        return PlatformInfo(os=os_name, arch=arch, backend=backend, cuda_version=cuda_version)

    def _binary_path(self, build_tag: str) -> Path:
        binary_name = _SERVER_BINARY_NAME.get(sys.platform, "llama-server")
        return self.cache_dir / build_tag / binary_name

    def _select_backend(self) -> tuple[BackendType, str | None]:
        nvidia_driver = self._probe_nvidia_driver()
        if nvidia_driver:
            return BackendType.CUDA, nvidia_driver
        if self._probe_vulkan():
            return BackendType.VULKAN, None
        return BackendType.CPU, None

    def _probe_nvidia_driver(self) -> str | None:
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi is None:
            return None
        try:
            result = subprocess.run(  # noqa: S603
                [nvidia_smi, "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout.strip().splitlines()[0].strip()

    def _probe_vulkan(self) -> bool:
        vulkaninfo = shutil.which("vulkaninfo")
        if vulkaninfo is None:
            return False
        try:
            result = subprocess.run(  # noqa: S603
                [vulkaninfo, "--summary"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _download_and_extract(self, build_tag: str, platform_info: PlatformInfo) -> None:
        asset_name = _asset_name(build_tag, platform_info.os, platform_info.arch, platform_info.backend)
        destination = self.cache_dir / build_tag
        destination.mkdir(parents=True, exist_ok=True)
        self._download_archive(f"{_RELEASE_DOWNLOAD_BASE}/{build_tag}/{asset_name}", destination, asset_name)

        if platform_info.backend == BackendType.CUDA and platform_info.os == "win32":
            cudart_asset = "cudart-llama-bin-win-cuda-12.4-x64.zip"
            self._download_archive(f"{_RELEASE_DOWNLOAD_BASE}/{build_tag}/{cudart_asset}", destination, cudart_asset)

    def _download_archive(self, url: str, destination: Path, asset_name: str) -> None:
        archive_path = destination / asset_name
        try:
            logger.info("Downloading llama.cpp asset: {}", url)
            with httpx.stream("GET", url, timeout=600.0, follow_redirects=True) as response:
                response.raise_for_status()
                with archive_path.open("wb") as output:
                    for chunk in response.iter_bytes(chunk_size=_DOWNLOAD_CHUNK_BYTES):
                        output.write(chunk)
        except httpx.HTTPError as exc:
            archive_path.unlink(missing_ok=True)
            msg = f"Download failed: {url}"
            raise BinaryDownloadError(msg) from exc

        try:
            if asset_name.endswith(".zip"):
                self._extract_zip(archive_path, destination)
            elif asset_name.endswith(".tar.gz"):
                self._extract_tar(archive_path, destination)
            else:
                msg = f"Unknown archive format: {asset_name}"
                raise BinaryDownloadError(msg)
        finally:
            archive_path.unlink(missing_ok=True)

    def _extract_zip(self, archive_path: Path, destination: Path) -> None:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir() or ".." in member.filename or member.filename.startswith("/"):
                    continue
                target = destination / Path(member.filename).name
                with archive.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)

    def _extract_tar(self, archive_path: Path, destination: Path) -> None:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or ".." in member.name or member.name.startswith("/"):
                    continue
                source = archive.extractfile(member)
                if source is None:
                    continue
                target = destination / Path(member.name).name
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
