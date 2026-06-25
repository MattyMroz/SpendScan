"""Folder management endpoints for organising receipts into named groups."""

from fastapi import APIRouter, HTTPException

from spendscan.api.dependencies import SessionDep
from spendscan.auth import CurrentUser
from spendscan.db.repositories import FolderRepository
from spendscan.models import Folder, FolderReceipt

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("")
def list_folders(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[Folder]:
    """Return all folders owned by the authenticated user."""
    repo = FolderRepository(session)

    if current_user.id is None:
        raise HTTPException(
            status_code=401,
            detail="User ID is missing",
        )

    return repo.list_folders(
        user_id=current_user.id,
    )


@router.post("")
def create_folder(
    payload: dict[str, str],
    session: SessionDep,
    current_user: CurrentUser,
) -> Folder:
    """Create a new named folder for the authenticated user."""
    repo = FolderRepository(session)

    if current_user.id is None:
        raise HTTPException(
            status_code=401,
            detail="User ID is missing",
        )

    return repo.create_folder(
        user_id=current_user.id,
        name=payload["name"],
        description=payload.get("description"),
    )


@router.post("/{folder_id}/receipts/{receipt_id}")
def assign_receipt(
    folder_id: int,
    receipt_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> FolderReceipt:
    """Add a receipt to an existing folder."""
    repo = FolderRepository(session)

    try:
        return repo.assign_receipt(
            folder_id=folder_id,
            receipt_id=receipt_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.delete("/{folder_id}/receipts/{receipt_id}")
def remove_receipt(
    folder_id: int,
    receipt_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, bool]:
    """Remove a receipt from a folder without deleting the receipt itself."""
    repo = FolderRepository(session)

    repo.remove_receipt(
        folder_id=folder_id,
        receipt_id=receipt_id,
    )

    return {"success": True}


@router.patch("/{folder_id}")
def update_folder(
    folder_id: int,
    payload: dict[str, str | None],
    session: SessionDep,
    current_user: CurrentUser,
) -> Folder:
    """Update mutable fields (e.g. description) of an existing folder."""
    repo = FolderRepository(session)

    folder = repo.update_folder(
        folder_id=folder_id,
        user_id=current_user.id,
        description=payload.get("description"),
    )

    if folder is None:
        raise HTTPException(
            status_code=404,
            detail="Folder not found",
        )

    return folder


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, bool]:
    """Delete a folder and its receipt associations (receipts themselves are kept)."""
    repo = FolderRepository(session)

    repo.delete_folder(
        folder_id=folder_id,
    )

    return {"success": True}
