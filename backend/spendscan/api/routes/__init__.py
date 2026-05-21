"""API route exports."""

from __future__ import annotations

from .analytics import router as analytics_router
from .health import router as health_router
from .receipts import router as receipts_router

__all__ = ["analytics_router", "health_router", "receipts_router"]
