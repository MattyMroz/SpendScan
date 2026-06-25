"""Async OCR service facade over the synchronous PaddleOCR-VL engine.

Wraps the blocking PaddleOcrEngine in asyncio-compatible calls using
``asyncio.to_thread`` so the engine never blocks the event loop.

Typical usage:

    service = OcrService()
    await service.initialize()
    result = await service.recognize(image_path)
    await service.cleanup()
"""

from __future__ import annotations

import asyncio
from typing import Any

from .paddle import PaddleOcrConfig, PaddleOcrEngine
from .protocols import OcrEngine
from .types import ImageInput, OcrResult


class OcrService:
    """Async facade over the synchronous PaddleOCR-VL engine.

    Delegates all blocking work to a thread pool via ``asyncio.to_thread``.
    Initialization is lazy: the engine starts on the first ``recognize`` call
    unless ``initialize`` is called explicitly.

    Attributes:
        config: Engine configuration used when creating a default engine.
    """

    __slots__ = ("_engine", "_init_lock", "config")

    def __init__(self, config: PaddleOcrConfig | None = None, *, engine: OcrEngine | None = None) -> None:
        """Initialize the service with optional config or a pre-built engine.

        Args:
            config: PaddleOCR-VL engine configuration. Loaded from application
                settings when ``None``.
            engine: Pre-initialized engine instance. Skips internal engine
                creation when provided (useful for testing).
        """
        self.config = config or PaddleOcrConfig.from_settings()
        self._engine: OcrEngine | None = engine
        self._init_lock = asyncio.Lock()

    @property
    def is_available(self) -> bool:
        """Whether the OCR engine is initialized and ready to process images."""
        return self._engine is not None and self._engine.is_available

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the OCR engine in a worker thread.

        Thread-safe: concurrent callers share the lock so the engine is
        created only once. A no-op when the engine is already initialized.

        Args:
            **kwargs: Extra keyword arguments forwarded to the engine's
                ``initialize`` method.
        """
        async with self._init_lock:
            if self._engine is not None:
                return
            engine = PaddleOcrEngine(self.config)
            await asyncio.to_thread(engine.initialize, **kwargs)
            self._engine = engine

    async def recognize(self, image: ImageInput, **kwargs: Any) -> OcrResult:
        """Recognize text in an image asynchronously.

        Triggers lazy initialization when the engine has not been started yet.

        Args:
            image: Image to process — file path, numpy array, or PIL image.
            **kwargs: Extra keyword arguments forwarded to the engine's
                ``recognize`` method (e.g. ``prompt``, ``max_dimension``).

        Returns:
            OCR result containing extracted text and per-line details.

        Raises:
            RuntimeError: If the engine cannot be initialized.
        """
        if self._engine is None:
            await self.initialize()
        if self._engine is None:
            msg = "OCR engine is not initialized"
            raise RuntimeError(msg)
        return await asyncio.to_thread(self._engine.recognize, image, **kwargs)

    async def cleanup(self) -> None:
        """Release OCR engine resources in a worker thread.

        Safe to call even when the engine was never started.
        Sets the internal engine reference to ``None`` after cleanup.
        """
        if self._engine is not None:
            await asyncio.to_thread(self._engine.cleanup)
            self._engine = None
