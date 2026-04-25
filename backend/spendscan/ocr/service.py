"""Async OCR service facade."""

from __future__ import annotations

import asyncio
from typing import Any

from .protocols import OcrEngine
from .qianfan import QianfanOcrConfig, QianfanOcrEngine
from .types import ImageInput, OcrResult


class OcrService:
    """Small async facade over the sync Qianfan OCR engine."""

    __slots__ = ("_engine", "_init_lock", "config")

    def __init__(self, config: QianfanOcrConfig | None = None, *, engine: OcrEngine | None = None) -> None:
        self.config = config or QianfanOcrConfig.from_settings()
        self._engine: OcrEngine | None = engine
        self._init_lock = asyncio.Lock()

    @property
    def is_available(self) -> bool:
        """Return whether the OCR engine is ready."""
        return self._engine is not None and self._engine.is_available

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize OCR engine in a worker thread."""
        if self._engine is not None:
            return
        async with self._init_lock:
            engine = QianfanOcrEngine(self.config)
            await asyncio.to_thread(engine.initialize, **kwargs)
            self._engine = engine

    async def recognize(self, image: ImageInput, **kwargs: Any) -> OcrResult:
        """Recognize receipt text asynchronously."""
        if self._engine is None:
            await self.initialize()
        if self._engine is None:
            msg = "OCR engine is not initialized"
            raise RuntimeError(msg)
        return await asyncio.to_thread(self._engine.recognize, image, **kwargs)

    async def cleanup(self) -> None:
        """Release OCR runtime resources."""
        if self._engine is not None:
            await asyncio.to_thread(self._engine.cleanup)
            self._engine = None
