"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from spendscan import __version__
from spendscan.config import Settings, get_settings

from .routes.health import router as health_router
from .routes.receipts import router as receipts_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create configured SpendScan FastAPI app."""
    resolved_settings = settings or get_settings()
    app = FastAPI(title="SpendScan API", version=__version__)
    app.include_router(health_router)
    app.include_router(receipts_router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()
