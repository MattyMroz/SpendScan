"""FastAPI application factory."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from spendscan import __version__
from spendscan.config import Settings, get_settings
from spendscan.db.database import get_session

from .routes.health import router as health_router
from .routes.receipts import router as receipts_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create configured SpendScan FastAPI app."""
    resolved_settings = settings or get_settings()
    app = FastAPI(title="SpendScan API", version=__version__)

    app.include_router(health_router)
    app.include_router(receipts_router, prefix=resolved_settings.api_prefix)

    @app.get("/health/db", tags=["health"])
    def database_health_check(
        session: Annotated[Session, Depends(get_session)],
    ) -> dict[str, str]:
        session.exec(select(1)).one()
        return {"status": "ok", "database": "connected"}

    return app


app = create_app()
