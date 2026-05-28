"""FastAPI application factory."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from starlette.responses import Response

from spendscan import __version__
from spendscan.config import Settings, get_settings
from spendscan.db.database import get_session

from .routes.analytics import router as analytics_router
from .routes.health import router as health_router
from .routes.receipts import router as receipts_router

request_logger = logging.getLogger("uvicorn.error")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create configured SpendScan FastAPI app."""
    resolved_settings = settings or get_settings()
    app = FastAPI(title="SpendScan API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
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

    @app.get("/health/db", tags=["health"])
    def database_health_check(
        session: Annotated[Session, Depends(get_session)],
    ) -> dict[str, str]:
        session.exec(select(1)).one()
        return {"status": "ok", "database": "connected"}

    return app


app = create_app()
