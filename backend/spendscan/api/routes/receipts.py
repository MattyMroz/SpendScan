"""Receipt OCR and analysis endpoints."""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path
from typing import Annotated, Final

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from spendscan.api.dependencies import ReceiptPipelineDep
from spendscan.api.schemas import OcrLineResponse, OcrResponse, ReceiptAnalyzeResponse
from spendscan.errors import ConfigurationError, ExternalServiceError, OutputValidationError

router = APIRouter(prefix="/receipts", tags=["receipts"])
_UPLOAD_CHUNK_BYTES: Final[int] = 1024 * 1024
ReceiptUpload = Annotated[UploadFile, File(...)]


@router.post("/ocr", response_model=OcrResponse)
async def ocr_receipt(
    pipeline: ReceiptPipelineDep,
    file: ReceiptUpload,
) -> OcrResponse:
    """Run OCR against an uploaded receipt image."""
    image_path = await _save_upload(file)
    try:
        result = await pipeline.recognize_image(image_path)
        return OcrResponse(
            text=result.text,
            lines=[
                OcrLineResponse(text=line.text, confidence=line.confidence, bbox=line.bbox) for line in result.lines
            ],
            engine=result.engine,
            processing_time_ms=result.processing_time_ms,
            image_shape=result.image_shape,
            error=result.error,
        )
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    finally:
        _cleanup_temp_file(image_path)
        await file.close()


@router.post("/analyze", response_model=ReceiptAnalyzeResponse)
async def analyze_receipt(
    pipeline: ReceiptPipelineDep,
    file: ReceiptUpload,
) -> ReceiptAnalyzeResponse:
    """Run OCR and Gemini JSON extraction against an uploaded receipt image."""
    image_path = await _save_upload(file)
    try:
        result = await pipeline.analyze_image(image_path)
        return ReceiptAnalyzeResponse.model_validate(result)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OutputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    finally:
        _cleanup_temp_file(image_path)
        await file.close()


async def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "receipt.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        while chunk := await file.read(_UPLOAD_CHUNK_BYTES):
            temporary_file.write(chunk)
        return Path(temporary_file.name)


def _cleanup_temp_file(path: Path) -> None:
    with contextlib.suppress(OSError):
        path.unlink(missing_ok=True)
