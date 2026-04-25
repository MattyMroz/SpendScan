"""API response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from spendscan.llm import ReceiptPipelineResult


class OcrLineResponse(BaseModel):
    """OCR line returned by the API."""

    model_config = ConfigDict(extra="forbid")
    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None


class OcrResponse(BaseModel):
    """OCR debug endpoint response."""

    model_config = ConfigDict(extra="forbid")
    text: str
    lines: list[OcrLineResponse]
    engine: str
    processing_time_ms: float
    image_shape: tuple[int, int]
    error: str | None = None


class ReadinessResponse(BaseModel):
    """Health readiness response."""

    model_config = ConfigDict(extra="forbid")
    ready: bool
    checks: dict[str, bool]


class ReceiptAnalyzeResponse(ReceiptPipelineResult):
    """Full receipt analysis endpoint response."""
