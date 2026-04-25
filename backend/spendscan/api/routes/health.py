"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import JSONResponse

from spendscan.api.dependencies import SettingsDep
from spendscan.api.schemas import ReadinessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    """Return liveness status."""
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessResponse)
def ready(settings: SettingsDep) -> ReadinessResponse | JSONResponse:
    """Return readiness status for configured OCR/LLM dependencies."""
    checks = {
        "gemini_api_key": bool(settings.gemini_api_key_value),
        "qianfan_model_dir_parent": settings.resolved_qianfan_model_dir.parent.exists(),
        "llama_cache_dir_parent": settings.resolved_llama_cache_dir.parent.exists(),
    }
    response = ReadinessResponse(ready=all(checks.values()), checks=checks)
    if response.ready:
        return response
    return JSONResponse(status_code=503, content=response.model_dump(mode="json"))
