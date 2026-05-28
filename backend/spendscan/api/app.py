"""FastAPI application factory."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from starlette.responses import JSONResponse, Response

from spendscan import __version__
from spendscan.config import Settings, get_settings
from spendscan.ocr import OcrService, PaddleOcrConfig

from .routes.analytics import router as analytics_router
from .routes.health import router as health_router
from .routes.receipts import router as receipts_router

request_logger = logging.getLogger("uvicorn.error")

DATABASE_UNAVAILABLE_MESSAGE = (
    "Database is unavailable. Start Docker Desktop and the spendscan-postgres container, then retry."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create configured SpendScan FastAPI app."""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        ocr = OcrService(PaddleOcrConfig.from_settings(resolved_settings))
        app.state.ocr_service = ocr
        request_logger.info("Preloading PaddleOCR-VL llama-server (this may take ~30s)...")
        start = time.perf_counter()
        try:
            await ocr.initialize()
        except Exception:
            request_logger.exception("OCR preload failed; engine will be unavailable")
        else:
            request_logger.info("OCR ready in %.1fs", time.perf_counter() - start)
        try:
            yield
        finally:
            request_logger.info("Shutting down OCR engine...")
            try:
                await ocr.cleanup()
            except Exception:
                request_logger.exception("OCR cleanup raised")

    app = FastAPI(title="SpendScan API", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(OperationalError)
    async def handle_database_operational_error(_: Request, exc: OperationalError) -> JSONResponse:
        request_logger.warning("Database unavailable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": DATABASE_UNAVAILABLE_MESSAGE},
        )

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.perf_counter()
        request_logger.info("HTTP start %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_logger.exception("HTTP error %s %s %.0f ms", request.method, request.url.path, elapsed_ms)
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        request_logger.info(
            "HTTP end %s %s %s %.0f ms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    app.include_router(health_router)
    app.include_router(receipts_router, prefix=resolved_settings.api_prefix)
    app.include_router(analytics_router, prefix=resolved_settings.api_prefix)

    return app


app = create_app()
