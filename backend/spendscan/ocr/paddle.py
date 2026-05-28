"""PaddleOCR-VL 1.5 (Q8) engine using GGUF files and llama-server.

Drop-in replacement for the Qianfan OCR engine. Downloads the model
and mmproj from Hugging Face on first use and serves it via llama-server.
"""

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

from spendscan.config import DEFAULT_LLAMA_BUILD_TAG, Settings, get_settings

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

PADDLE_MODEL_HF_REPO: Final[str] = "tristan-hjkl/PaddleOCR-VL-1.5-GGUF-Q8"
"""Hugging Face repo for the quantized language model (Q8_0)."""

PADDLE_MMPROJ_HF_REPO: Final[str] = "tristan-hjkl/PaddleOCR-VL-1.5-GGUF-Q8"
"""Hugging Face repo for the vision encoder (mmproj)."""

PADDLE_MODEL_FILENAME: Final[str] = "PaddleOCR-VL-1.5-Q8_0.gguf"
"""Quantized language model weights (~498 MB Q8_0)."""

PADDLE_MMPROJ_FILENAME: Final[str] = "PaddleOCR-VL-1.5-mmproj.gguf"
"""Vision encoder (mmproj) weights (~882 MB) — the f16 variant lacks image_mean metadata."""

DEFAULT_PROMPT: Final[str] = "Spotting:"
"""Native PaddleOCR-VL trigger prompt (one of 6 trained task tokens)."""

DEFAULT_MAX_TOKENS: Final[int] = 2048
DEFAULT_TEMPERATURE: Final[float] = 0.0
DEFAULT_REPEAT_PENALTY: Final[float] = 1.2
DEFAULT_REPEAT_LAST_N: Final[int] = -1
DEFAULT_GPU_LAYERS: Final[int] = -1
DEFAULT_CONTEXT_LENGTH: Final[int] = 32768
DEFAULT_MAX_IMAGE_DIMENSION: Final[int] = 2048
MAX_OOM_RETRIES: Final[int] = 2
OOM_FALLBACK_DIMENSIONS: Final[tuple[int, ...]] = (1024, 512)
_DOWNLOAD_CHUNK_BYTES: Final[int] = 1024 * 1024


@dataclass(slots=True)
class PaddleOcrConfig:
    """Configuration for the PaddleOCR-VL engine."""

    device: Literal["cuda", "cpu"] = "cuda"
    model_dir: Path | None = None
    llama_cache_dir: Path | None = None
    llama_build_tag: str | None = DEFAULT_LLAMA_BUILD_TAG
    max_image_dimension: int = DEFAULT_MAX_IMAGE_DIMENSION
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    repeat_penalty: float = DEFAULT_REPEAT_PENALTY
    repeat_last_n: int = DEFAULT_REPEAT_LAST_N
    n_gpu_layers: int = DEFAULT_GPU_LAYERS
    n_ctx: int = DEFAULT_CONTEXT_LENGTH
    default_prompt: str = DEFAULT_PROMPT

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> PaddleOcrConfig:
        """Create OCR config from application settings."""
        resolved_settings = settings or get_settings()
        return cls(
            model_dir=resolved_settings.resolved_paddle_model_dir,
            llama_cache_dir=resolved_settings.resolved_llama_cache_dir,
            llama_build_tag=resolved_settings.llama_build_tag,
        )

    def __post_init__(self) -> None:
        if self.device == "cpu":
            self.n_gpu_layers = 0


class PaddleModelResolver:
    """Download and resolve PaddleOCR-VL GGUF files from Hugging Face."""

    __slots__ = ("model_dir",)

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir

    def ensure_files(self) -> Path:
        """Ensure the model and mmproj files exist locally."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        for filename in required_paddle_files():
            destination = self.model_dir / filename
            if not destination.exists():
                self._download(filename, destination)
        return self.model_dir

    def _download(self, filename: str, destination: Path) -> None:
        url = paddle_download_url(filename)
        temp_path = destination.with_suffix(f"{destination.suffix}.tmp")
        try:
            logger.info("Downloading PaddleOCR-VL file: {}", filename)
            with httpx.stream("GET", url, timeout=1200.0, follow_redirects=True) as response:
                response.raise_for_status()
                with temp_path.open("wb") as output:
                    for chunk in response.iter_bytes(chunk_size=_DOWNLOAD_CHUNK_BYTES):
                        output.write(chunk)
            temp_path.replace(destination)
        except httpx.HTTPError as exc:
            temp_path.unlink(missing_ok=True)
            msg = f"Failed to download PaddleOCR-VL file from Hugging Face: {filename}"
            raise OcrConfigError(msg) from exc


def required_paddle_files() -> tuple[str, str]:
    """Return required PaddleOCR-VL files."""
    return PADDLE_MODEL_FILENAME, PADDLE_MMPROJ_FILENAME


def paddle_download_url(filename: str) -> str:
    """Build direct Hugging Face download URL for a PaddleOCR-VL file."""
    repo = PADDLE_MMPROJ_HF_REPO if filename == PADDLE_MMPROJ_FILENAME else PADDLE_MODEL_HF_REPO
    return f"https://huggingface.co/{repo}/resolve/main/{filename}"


class PaddleOcrEngine:
    """PaddleOCR-VL 1.5 engine backed by llama-server."""

    __slots__ = ("_client", "_model_dir", "_server", "config")

    def __init__(self, config: PaddleOcrConfig | None = None) -> None:
        self.config = config or PaddleOcrConfig.from_settings()
        self._server: LlamaServerManager | None = None
        self._client: LlamaClient | None = None
        self._model_dir: Path | None = None

    @property
    def name(self) -> str:
        """Return engine name."""
        return "paddle-ocr-vl"

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
            msg = "PaddleOCR-VL model directory is not configured"
            raise OcrConfigError(msg)
        self._model_dir = PaddleModelResolver(self.config.model_dir).ensure_files()

    def _start_server(self) -> None:
        if self._model_dir is None:
            msg = "PaddleOCR-VL model directory was not resolved"
            raise OcrEngineError(msg)
        model_file = self._model_dir / PADDLE_MODEL_FILENAME
        mmproj_file = self._model_dir / PADDLE_MMPROJ_FILENAME
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
            msg = f"Failed to start PaddleOCR-VL llama-server: {exc}"
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
            logger.warning("PaddleOCR-VL OOM retry {}/{} at {}px", attempt + 1, MAX_OOM_RETRIES, fallback)

        return OcrResult(error="GPU out of memory after retries", engine=self.name, image_shape=original_shape)

    def _run_inference(self, pil_image: Image.Image, prompt: str, original_shape: tuple[int, int]) -> OcrResult:
        if self._client is None:
            msg = "PaddleOCR-VL server is not started"
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
                repeat_penalty=self.config.repeat_penalty,
                repeat_last_n=self.config.repeat_last_n,
            )
        except LlamaRuntimeError as exc:
            msg = f"PaddleOCR-VL inference failed: {exc}"
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
