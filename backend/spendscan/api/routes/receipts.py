"""Receipt OCR, analysis, and persistence endpoints."""

from __future__ import annotations

import contextlib
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Final
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from spendscan.api.dependencies import ReceiptPipelineDep, SessionDep, SettingsDep
from spendscan.api.schemas import (
    OcrLineResponse,
    OcrResponse,
    ReceiptAnalyzeResponse,
    ReceiptBatchCreateResponse,
    ReceiptDetailResponse,
    ReceiptListItemResponse,
    ReceiptUpdateRequest,
    StoredReceiptImageResponse,
    StoredReceiptItemResponse,
)
from spendscan.auth import CurrentUser
from spendscan.config import project_root
from spendscan.db.repositories import FolderRepository, ReceiptDetailRecord, ReceiptImageCreate, ReceiptRepository
from spendscan.db.repositories.receipts import (
    cents_to_decimal,
    required_cents_to_decimal,
)
from spendscan.errors import ConfigurationError, ExternalServiceError, OutputValidationError
from spendscan.pipeline import MultiImageReceiptPipelineResult

router = APIRouter(prefix="/receipts", tags=["receipts"])
_UPLOAD_CHUNK_BYTES: Final[int] = 1024 * 1024
_PAIRED_RECEIPT_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^(?P<receipt>.+_\d+)_(?P<page>\d+)$")
ReceiptUpload = Annotated[UploadFile, File(...)]
ReceiptUploads = Annotated[list[UploadFile], File(...)]


@dataclass(frozen=True, slots=True)
class StoredUpload:
    """File saved from an API upload, held in memory for the duration of a request.

    Attributes:
        original_filename: Client-supplied filename at upload time.
        path: Temporary on-disk path used for pipeline processing.
        content_type: MIME type reported by the client, or None.
        image_data: Raw image bytes read once after writing to disk.
    """

    original_filename: str
    path: Path
    content_type: str | None
    image_data: bytes  # raw bytes, read once after saving to disk


@router.post("/ocr", response_model=OcrResponse)
async def ocr_receipt(
    pipeline: ReceiptPipelineDep,
    file: ReceiptUpload,
) -> OcrResponse:
    """Run OCR against an uploaded receipt image without saving it."""
    image_path = await _save_temp_upload(file)
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
    """Run OCR and Gemini extraction against one uploaded image without saving it."""
    image_path = await _save_temp_upload(file)
    try:
        result = await pipeline.analyze_image(image_path)
        return ReceiptAnalyzeResponse.model_validate(result.model_dump())
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OutputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    finally:
        _cleanup_temp_file(image_path)
        await file.close()


@router.post("/analyze/pages", response_model=ReceiptAnalyzeResponse)
async def analyze_receipt_pages(
    pipeline: ReceiptPipelineDep,
    files: ReceiptUploads,
) -> ReceiptAnalyzeResponse:
    """Run OCR and Gemini extraction against one multi-image receipt without saving it."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

    image_paths: list[Path] = []
    try:
        image_paths = [await _save_temp_upload(file) for file in files]
        result = await pipeline.analyze_images(tuple(image_paths))
        return ReceiptAnalyzeResponse.model_validate(result.receipt.model_dump())
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OutputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    finally:
        for image_path in image_paths:
            _cleanup_temp_file(image_path)
        for file in files:
            await file.close()


@router.post("", response_model=ReceiptDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
    pipeline: ReceiptPipelineDep,
    settings: SettingsDep,
    session: SessionDep,
    current_user: CurrentUser,
    files: ReceiptUploads,
) -> ReceiptDetailResponse:
    """Analyze one receipt made of one or more uploaded images and save it to the database."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    uploads = await _save_uploads(files, settings.resolved_upload_dir)
    try:
        pipeline_result = await pipeline.analyze_images(tuple(upload.path for upload in uploads))
        detail = _save_pipeline_result(
            session, uploads=uploads, pipeline_result=pipeline_result, user_id=current_user.id
        )
    except ConfigurationError as exc:
        _cleanup_uploads(uploads)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OutputValidationError as exc:
        _cleanup_uploads(uploads)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        _cleanup_uploads(uploads)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception:
        _cleanup_uploads(uploads)
        raise
    finally:
        # Always clean up temp files on disk — bytes are already in DB
        _cleanup_uploads(uploads)
    return _detail_response(detail)


@router.post("/batch", response_model=ReceiptBatchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt_batch(
    pipeline: ReceiptPipelineDep,
    settings: SettingsDep,
    session: SessionDep,
    current_user: CurrentUser,
    files: ReceiptUploads,
) -> ReceiptBatchCreateResponse:
    """Analyze multiple receipts and save each one, grouping files named like receipt_001_1.png."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")

    uploads = await _save_uploads(files, settings.resolved_upload_dir)
    details: list[ReceiptDetailResponse] = []
    try:
        upload_groups = _group_uploads_by_receipt(uploads)
        pipeline_results = await pipeline.analyze_receipt_groups(
            tuple(tuple(upload.path for upload in group) for group in upload_groups)
        )
        for upload_group, pipeline_result in zip(upload_groups, pipeline_results, strict=True):
            detail = _save_pipeline_result(
                session, uploads=upload_group, pipeline_result=pipeline_result, user_id=current_user.id
            )
            details.append(_detail_response(detail))
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OutputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    finally:
        _cleanup_uploads(uploads)
    return ReceiptBatchCreateResponse(receipts=details)


@router.get("", response_model=list[ReceiptListItemResponse])
def list_receipts(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: Annotated[date | None, Query(description="Inclusive receipt date start filter.")] = None,
    end_date: Annotated[date | None, Query(description="Inclusive receipt date end filter.")] = None,
    merchant_name: Annotated[str | None, Query(description="Case-insensitive merchant name substring.")] = None,
) -> list[ReceiptListItemResponse]:
    """List persisted receipts for the authenticated user."""
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User id missing",
        )

    repository = ReceiptRepository(session)
    folder_repo = FolderRepository(session)

    receipts = repository.list_receipts(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        merchant_name=merchant_name,
    )

    responses: list[ReceiptListItemResponse] = []

    for receipt in receipts:
        if receipt.id is None:
            continue

        detail = repository.get_detail(
            receipt.id,
            user_id=current_user.id,
        )

        if detail is None:
            continue

        folder_ids = folder_repo.get_receipt_folder_ids(
            receipt.id,
        )

        responses.append(
            ReceiptListItemResponse(
                id=receipt.id,
                status=receipt.status,
                merchant_name=receipt.merchant_name,
                receipt_date=receipt.receipt_date,
                currency=receipt.currency,
                total_amount=required_cents_to_decimal(receipt.total_amount),
                description=receipt.description,
                importance=receipt.importance,
                image_count=len(detail.images),
                item_count=len(detail.items),
                created_at=receipt.created_at,
                folder_ids=folder_ids,
            )
        )

    return responses


@router.get("/{receipt_id}", response_model=ReceiptDetailResponse)
def get_receipt(receipt_id: int, session: SessionDep, current_user: CurrentUser) -> ReceiptDetailResponse:
    """Return one persisted receipt with images and items."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    detail = ReceiptRepository(session).get_detail(receipt_id, user_id=current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return _detail_response(detail)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(receipt_id: int, session: SessionDep, current_user: CurrentUser) -> None:
    """Delete a persisted receipt and any legacy stored upload files."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    detail = ReceiptRepository(session).delete_receipt(receipt_id, user_id=current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    # Best-effort cleanup of any legacy on-disk files (new uploads have no stored_path)
    _cleanup_stored_receipt_files(detail)


@router.patch("/{receipt_id}", response_model=ReceiptDetailResponse)
def update_receipt(
    receipt_id: int,
    payload: ReceiptUpdateRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ReceiptDetailResponse:
    """Patch editable fields of a persisted receipt."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    items_payload: list[dict[str, object]] | None = None
    if payload.items is not None:
        items_payload = [item.model_dump() for item in payload.items]
    detail = ReceiptRepository(session).update_receipt(
        receipt_id,
        user_id=current_user.id,
        merchant_name=payload.merchant_name,
        receipt_date=payload.receipt_date,
        currency=payload.currency,
        total_amount=payload.total_amount,
        payment_method=payload.payment_method,
        description=payload.description,
        importance=payload.importance,
        items=items_payload,
    )
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return _detail_response(detail)


@router.get("/{receipt_id}/images/{image_id}")
def get_receipt_image(
    receipt_id: int,
    image_id: int,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
) -> Response:
    """Stream a stored receipt image owned by the current user.

    Serves from DB bytes when available; falls back to disk for legacy records.
    """
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    detail = ReceiptRepository(session).get_detail(receipt_id, user_id=current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    image = next((img for img in detail.images if img.id == image_id), None)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    media_type = image.content_type or "image/png"

    # Primary: serve bytes stored in the database
    if image.image_data:
        return Response(content=image.image_data, media_type=media_type)

    # Fallback: serve from disk (legacy records created before migration)
    if image.stored_path:
        file_path = project_root() / image.stored_path
        if file_path.exists():
            return FileResponse(file_path, media_type=media_type)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image data not available")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _save_temp_upload(file: UploadFile) -> Path:
    """Stream an upload to a temporary file and return its path.

    Args:
        file: FastAPI upload file object.

    Returns:
        Path to the newly created temporary file.
    """
    suffix = Path(file.filename or "receipt.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        while chunk := await file.read(_UPLOAD_CHUNK_BYTES):
            temporary_file.write(chunk)
        return Path(temporary_file.name)


async def _save_uploads(files: list[UploadFile], upload_dir: Path) -> tuple[StoredUpload, ...]:
    """Save a list of uploads into a unique batch subdirectory and read their bytes.

    Creates a UUID-named subdirectory under upload_dir and writes each file
    to it sequentially. On any error the batch directory is removed before
    re-raising.

    Args:
        files: FastAPI upload file objects to persist.
        upload_dir: Base directory for batch subdirectories.

    Returns:
        Tuple of StoredUpload instances in the same order as files.

    Raises:
        HTTPException: 400 if files is empty or any individual file is empty.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

    batch_dir = upload_dir / uuid4().hex
    batch_dir.mkdir(parents=True, exist_ok=False)
    uploads: list[StoredUpload] = []
    try:
        for index, file in enumerate(files, start=1):
            original_filename = Path(file.filename or f"receipt_{index}.png").name
            suffix = Path(original_filename).suffix.lower() or ".png"
            target_path = batch_dir / f"page_{index:03d}{suffix}"
            with target_path.open("wb") as output_file:
                while chunk := await file.read(_UPLOAD_CHUNK_BYTES):
                    output_file.write(chunk)
            if target_path.stat().st_size == 0:
                _raise_empty_upload(original_filename)
            image_data = target_path.read_bytes()
            uploads.append(
                StoredUpload(
                    original_filename=original_filename,
                    path=target_path,
                    content_type=file.content_type,
                    image_data=image_data,
                )
            )
        return tuple(uploads)
    except Exception:
        _cleanup_directory(batch_dir)
        raise
    finally:
        for file in files:
            await file.close()


def _group_uploads_by_receipt(uploads: tuple[StoredUpload, ...]) -> tuple[tuple[StoredUpload, ...], ...]:
    """Group uploads into per-receipt tuples using the paired-receipt naming convention.

    Files whose stem matches ``<name>_<page>`` (e.g. ``receipt_001_1.png``,
    ``receipt_001_2.png``) are grouped together in page order under the shared
    receipt name.  Files that do not match are treated as standalone receipts.

    Args:
        uploads: All uploads from a batch request.

    Returns:
        Tuple of upload groups; each inner tuple contains the pages of one receipt.

    Raises:
        HTTPException: 400 if the same page number appears twice in a group.
    """
    paired_groups: dict[str, dict[int, StoredUpload]] = {}
    standalone_groups: list[tuple[StoredUpload, ...]] = []
    for upload in uploads:
        match = _PAIRED_RECEIPT_NAME_RE.match(Path(upload.original_filename).stem)
        if match is None:
            standalone_groups.append((upload,))
            continue

        receipt_name = match.group("receipt")
        page_number = int(match.group("page"))
        pages = paired_groups.setdefault(receipt_name, {})
        if page_number in pages:
            msg = f"Duplicate page {page_number} for receipt group {receipt_name}"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        pages[page_number] = upload

    grouped_uploads = [
        tuple(upload for _, upload in sorted(pages.items())) for _, pages in sorted(paired_groups.items())
    ]
    return tuple(grouped_uploads + standalone_groups)


def _save_pipeline_result(
    session: Session,
    *,
    uploads: tuple[StoredUpload, ...],
    pipeline_result: MultiImageReceiptPipelineResult,
    user_id: int,
) -> ReceiptDetailRecord:
    """Persist a pipeline result and its image pages to the database.

    Builds ReceiptImageCreate records from the pipeline output and the
    in-memory image bytes, then delegates to the repository.

    Args:
        session: Active SQLModel session.
        uploads: Ordered upload objects whose bytes are stored in the DB.
        pipeline_result: OCR + extraction result for all pages.
        user_id: Owner of the new receipt record.

    Returns:
        ReceiptDetailRecord with the newly assigned database IDs.
    """
    images = tuple(
        ReceiptImageCreate(
            page_number=result.page_number,
            original_filename=uploads[result.page_number - 1].original_filename,
            stored_path=None,  # no longer saved to disk permanently
            image_data=uploads[result.page_number - 1].image_data,
            content_type=uploads[result.page_number - 1].content_type,
            ocr_text=result.ocr.text,
            ocr_engine=result.ocr.engine,
            ocr_processing_time_ms=result.ocr.processing_time_ms,
            image_shape=result.ocr.image_shape,
        )
        for result in pipeline_result.images
    )
    return ReceiptRepository(session).save_analysis(result=pipeline_result.receipt, images=images, user_id=user_id)


def _detail_response(detail: ReceiptDetailRecord) -> ReceiptDetailResponse:
    """Convert a ReceiptDetailRecord from the repository into a ReceiptDetailResponse.

    Args:
        detail: Repository record containing the receipt, images, and items.

    Returns:
        Serialisable API response with all monetary amounts as Decimal.

    Raises:
        RuntimeError: If any persisted entity is missing a database ID.
    """
    receipt = detail.receipt
    receipt_id = _required_id(receipt.id, "receipt")
    return ReceiptDetailResponse(
        id=receipt_id,
        status=detail.receipt.status,
        merchant_name=detail.receipt.merchant_name,
        receipt_date=detail.receipt.receipt_date,
        currency=detail.receipt.currency,
        subtotal_amount=cents_to_decimal(receipt.subtotal_amount),
        tax_amount=cents_to_decimal(receipt.tax_amount),
        total_amount=required_cents_to_decimal(receipt.total_amount),
        total_discount_amount=cents_to_decimal(receipt.total_discount_amount),
        payment_method=detail.receipt.payment_method,
        description=detail.receipt.description,
        raw_ocr_text=detail.receipt.raw_ocr_text,
        warnings=detail.receipt.warnings,
        error=detail.receipt.error,
        importance=detail.receipt.importance,
        created_at=detail.receipt.created_at,
        images=[
            StoredReceiptImageResponse(
                id=_required_id(image.id, "receipt image"),
                page_number=image.page_number,
                original_filename=image.original_filename,
                stored_path=image.stored_path or "",
                content_type=image.content_type,
                ocr_text=image.ocr_text,
                ocr_engine=image.ocr_engine,
                ocr_processing_time_ms=image.ocr_processing_time_ms,
                image_width=image.image_width,
                image_height=image.image_height,
            )
            for image in detail.images
        ],
        items=[
            StoredReceiptItemResponse(
                id=_required_id(item.item.id, "receipt item"),
                product_name=item.item.product_name,
                quantity=item.item.quantity,
                unit_price=cents_to_decimal(item.item.unit_price),
                total_price=required_cents_to_decimal(item.item.total_price),
                discount_amount=cents_to_decimal(item.item.discount_amount),
                category=item.category_name,
            )
            for item in detail.items
        ],
    )


def _cleanup_uploads(uploads: tuple[StoredUpload, ...]) -> None:
    """Remove the temporary batch directory created during upload processing."""
    if not uploads:
        return
    # All uploads land in the same batch_dir; remove via the first file's parent
    batch_dir = uploads[0].path.parent
    _cleanup_directory(batch_dir)


def _cleanup_stored_receipt_files(detail: ReceiptDetailRecord) -> None:
    """Best-effort removal of legacy on-disk image files (stored_path rows)."""
    for image in detail.images:
        if image.stored_path:
            _cleanup_stored_path(Path(image.stored_path))


def _cleanup_stored_path(path: Path) -> None:
    """Delete a legacy on-disk image file and remove its directory if now empty."""
    resolved_path = path if path.is_absolute() else project_root() / path
    with contextlib.suppress(OSError):
        resolved_path.unlink(missing_ok=True)
    parent = resolved_path.parent
    with contextlib.suppress(OSError):
        if parent != project_root() and not any(parent.iterdir()):
            parent.rmdir()


def _cleanup_directory(path: Path) -> None:
    """Recursively delete a directory, silencing OS errors."""
    with contextlib.suppress(OSError):
        shutil.rmtree(path)


def _raise_empty_upload(filename: str) -> None:
    """Raise a 400 HTTPException indicating that the uploaded file has no content."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{filename} is empty")


def _cleanup_temp_file(path: Path) -> None:
    """Delete a single temporary file, silencing OS errors."""
    with contextlib.suppress(OSError):
        path.unlink(missing_ok=True)


def _required_id(value: int | None, entity_name: str) -> int:
    """Return value as a non-None int, raising RuntimeError if it is None.

    Args:
        value: Database primary key that should have been assigned on persist.
        entity_name: Human-readable name used in the error message.

    Returns:
        The integer primary key.

    Raises:
        RuntimeError: If value is None, indicating a persistence bug.
    """
    if value is None:
        msg = f"Persisted {entity_name} is missing an id"
        raise RuntimeError(msg)
    return value
