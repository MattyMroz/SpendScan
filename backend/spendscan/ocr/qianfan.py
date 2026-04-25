"""Qianfan OCR engine using GGUF files and llama-server."""

from __future__ import annotations

import base64
import io
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

import httpx
from loguru import logger
from PIL import Image

from spendscan.config import Settings, get_settings

from .errors import OcrConfigError, OcrEngineError
from .llama_runtime import (
    BinaryResolver,
    ChatMessage,
    ContentPart,
    LlamaRuntimeConfig,
    LlamaRuntimeError,
    LlamaServerManager,
    prepare_llama_binary,
)
from .llama_runtime.client import LlamaClient
from .types import ImageInput, OcrLine, OcrResult
from .utils import cleanup_gpu_memory, get_fallback_dimension, parse_ocr_output, validate_and_resize_image

QIANFAN_HF_REPO: Final[str] = "Reza2kn/Qianfan-OCR-GGUF"
"""Hugging Face repository used for Qianfan OCR models."""

GGUF_VARIANTS: Final[dict[str, str]] = {
    "bf16": "Qianfan-OCR-bf16.gguf",
    "q8_0": "Qianfan-OCR-q8_0.gguf",
    "q4_k_m": "Qianfan-OCR-q4_k_m.gguf",
}
MMPROJ_FILENAME: Final[str] = "Qianfan-OCR-mmproj-f16.gguf"
DEFAULT_VARIANT: Final[str] = "q4_k_m"
DEFAULT_PROMPT: Final[str] = (
    "OCR all text in the receipt image. Return plain text with line breaks. "
    "Keep product names, dates, totals, tax values, punctuation, and prices exactly as visible."
)
DEFAULT_MAX_TOKENS: Final[int] = 1024
DEFAULT_TEMPERATURE: Final[float] = 0.0
DEFAULT_GPU_LAYERS: Final[int] = -1
DEFAULT_CONTEXT_LENGTH: Final[int] = 4096
DEFAULT_MAX_IMAGE_DIMENSION: Final[int] = 2048
MAX_OOM_RETRIES: Final[int] = 2
OOM_FALLBACK_DIMENSIONS: Final[tuple[int, ...]] = (1024, 512)
_DOWNLOAD_CHUNK_BYTES: Final[int] = 1024 * 1024


@dataclass(slots=True)
class QianfanOcrConfig:
    """Configuration for the Qianfan OCR engine."""

    device: Literal["cuda", "cpu"] = "cuda"
    variant: str = DEFAULT_VARIANT
    model_dir: Path | None = None
    llama_cache_dir: Path | None = None
    llama_build_tag: str | None = None
    max_image_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    n_gpu_layers: int = DEFAULT_GPU_LAYERS
    n_ctx: int = DEFAULT_CONTEXT_LENGTH
    default_prompt: str = DEFAULT_PROMPT

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> QianfanOcrConfig:
        """Create OCR config from application settings."""
        resolved_settings = settings or get_settings()
        return cls(
            model_dir=resolved_settings.resolved_qianfan_model_dir,
            llama_cache_dir=resolved_settings.resolved_llama_cache_dir,
            llama_build_tag=resolved_settings.llama_build_tag,
        )

    def __post_init__(self) -> None:
        if self.device == "cpu":
            self.n_gpu_layers = 0
        if self.variant not in GGUF_VARIANTS:
            available = ", ".join(sorted(GGUF_VARIANTS))
            msg = f"Unknown Qianfan OCR variant {self.variant!r}. Available: {available}"
            raise OcrConfigError(msg)


class QianfanModelResolver:
    """Download and resolve Qianfan OCR GGUF files from Hugging Face."""

    __slots__ = ("model_dir",)

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir

    def ensure_files(self, variant: str = DEFAULT_VARIANT) -> Path:
        """Ensure the selected model and mmproj files exist locally."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        for filename in required_qianfan_files(variant):
            destination = self.model_dir / filename
            if not destination.exists():
                self._download(filename, destination)
        return self.model_dir

    def _download(self, filename: str, destination: Path) -> None:
        url = qianfan_download_url(filename)
        temp_path = destination.with_suffix(f"{destination.suffix}.tmp")
        try:
            logger.info("Downloading Qianfan OCR file: {}", filename)
            with httpx.stream("GET", url, timeout=1200.0, follow_redirects=True) as response:
                response.raise_for_status()
                with temp_path.open("wb") as output:
                    for chunk in response.iter_bytes(chunk_size=_DOWNLOAD_CHUNK_BYTES):
                        output.write(chunk)
            temp_path.replace(destination)
        except httpx.HTTPError as exc:
            temp_path.unlink(missing_ok=True)
            msg = f"Failed to download Qianfan OCR file from Hugging Face: {filename}"
            raise OcrConfigError(msg) from exc


def required_qianfan_files(variant: str = DEFAULT_VARIANT) -> tuple[str, str]:
    """Return required Qianfan files for a model variant."""
    try:
        model_filename = GGUF_VARIANTS[variant]
    except KeyError as exc:
        msg = f"Unknown Qianfan OCR variant: {variant}"
        raise OcrConfigError(msg) from exc
    return model_filename, MMPROJ_FILENAME


def qianfan_download_url(filename: str) -> str:
    """Build direct Hugging Face download URL for a Qianfan file."""
    return f"https://huggingface.co/{QIANFAN_HF_REPO}/resolve/main/{filename}"


class QianfanOcrEngine:
    """Qianfan OCR engine backed by llama-server."""

    __slots__ = ("_client", "_model_dir", "_server", "config")

    def __init__(self, config: QianfanOcrConfig | None = None) -> None:
        self.config = config or QianfanOcrConfig.from_settings()
        self._server: LlamaServerManager | None = None
        self._client: LlamaClient | None = None
        self._model_dir: Path | None = None

    @property
    def name(self) -> str:
        """Return engine name."""
        return "qianfan-ocr"

    @property
    def is_available(self) -> bool:
        """Return whether llama-server is running."""
        return self._server is not None and self._server.is_running

    def initialize(self, **_kwargs: Any) -> None:
        """Resolve model files and start llama-server."""
        if self.is_available:
            return
        self._resolve_model_dir()
        self._start_server()

    def cleanup(self) -> None:
        """Stop llama-server and clear cached resources."""
        if self._server is not None:
            self._server.stop()
            self._server = None
            self._client = None
            cleanup_gpu_memory()

    def recognize(self, image: ImageInput, **kwargs: Any) -> OcrResult:
        """Extract receipt text from an image."""
        if not self.is_available:
            self.initialize()

        prompt = str(kwargs.get("prompt", self.config.default_prompt))
        max_dimension = int(kwargs.get("max_dimension", self.config.max_image_dimension))

        try:
            pil_image, original_shape, _was_resized = validate_and_resize_image(
                image,
                max_dimension=max_dimension,
            )
        except (FileNotFoundError, ValueError) as exc:
            return OcrResult(error=str(exc), engine=self.name)

        return self._recognize_with_oom_retry(pil_image, prompt, original_shape)

    def _resolve_model_dir(self) -> None:
        if self.config.model_dir is None:
            msg = "Qianfan model directory is not configured"
            raise OcrConfigError(msg)
        self._model_dir = QianfanModelResolver(self.config.model_dir).ensure_files(self.config.variant)

    def _start_server(self) -> None:
        if self._model_dir is None:
            msg = "Qianfan model directory was not resolved"
            raise OcrEngineError(msg)
        model_file = self._model_dir / GGUF_VARIANTS[self.config.variant]
        mmproj_file = self._model_dir / MMPROJ_FILENAME
        if not model_file.exists():
            msg = f"GGUF model not found: {model_file}"
            raise OcrConfigError(msg)
        if not mmproj_file.exists():
            msg = f"Vision encoder not found: {mmproj_file}"
            raise OcrConfigError(msg)

        build_tag = self._ensure_llama_binary()
        runtime_config = LlamaRuntimeConfig(n_gpu_layers=self.config.n_gpu_layers, n_ctx=self.config.n_ctx)
        resolver = BinaryResolver(self.config.llama_cache_dir)
        self._server = LlamaServerManager(runtime_config, binary_resolver=resolver)
        try:
            self._client = self._server.start(
                model_path=model_file,
                mmproj_path=mmproj_file,
                build_tag=build_tag,
            )
        except LlamaRuntimeError as exc:
            self._server = None
            msg = f"Failed to start Qianfan llama-server: {exc}"
            raise OcrEngineError(msg) from exc

    def _ensure_llama_binary(self) -> str:
        cache_dir = self.config.llama_cache_dir or get_settings().resolved_llama_cache_dir
        preparation = prepare_llama_binary(cache_dir, build_tag=self.config.llama_build_tag)
        self.config.llama_cache_dir = cache_dir
        self.config.llama_build_tag = preparation.build_tag
        return preparation.build_tag

    def _recognize_with_oom_retry(
        self,
        pil_image: Image.Image,
        prompt: str,
        original_shape: tuple[int, int],
    ) -> OcrResult:
        current_dimension = max(pil_image.width, pil_image.height)
        for attempt in range(MAX_OOM_RETRIES + 1):
            try:
                return self._run_inference(pil_image, prompt, original_shape)
            except OcrEngineError as exc:
                if "out of memory" not in str(exc).lower() and "oom" not in str(exc).lower():
                    return OcrResult(error=f"Inference error: {exc}", engine=self.name, image_shape=original_shape)

            cleanup_gpu_memory()
            fallback = get_fallback_dimension(current_dimension, OOM_FALLBACK_DIMENSIONS)
            if fallback is None:
                break
            pil_image.thumbnail((fallback, fallback), Image.Resampling.LANCZOS)
            current_dimension = fallback
            logger.warning("Qianfan OCR OOM retry {}/{} at {}px", attempt + 1, MAX_OOM_RETRIES, fallback)

        return OcrResult(error="GPU out of memory after retries", engine=self.name, image_shape=original_shape)

    def _run_inference(self, pil_image: Image.Image, prompt: str, original_shape: tuple[int, int]) -> OcrResult:
        if self._client is None:
            msg = "Qianfan OCR server is not started"
            raise OcrEngineError(msg)

        start = time.perf_counter()
        messages = [
            ChatMessage(
                role="user",
                content=[
                    ContentPart(type="image_url", image_url={"url": self._image_to_data_uri(pil_image)}),
                    ContentPart(type="text", text=prompt),
                ],
            ),
        ]
        try:
            response = self._client.chat(
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
        except LlamaRuntimeError as exc:
            msg = f"Qianfan OCR inference failed: {exc}"
            raise OcrEngineError(msg) from exc

        elapsed_ms = (time.perf_counter() - start) * 1000
        cleaned_text, text_lines = parse_ocr_output(response.content)
        return OcrResult(
            text=cleaned_text,
            lines=[OcrLine(text=line) for line in text_lines],
            engine=self.name,
            processing_time_ms=elapsed_ms,
            image_shape=original_shape,
        )

    @staticmethod
    def _image_to_data_uri(pil_image: Image.Image) -> str:
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
