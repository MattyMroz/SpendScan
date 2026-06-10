from fastapi import APIRouter, HTTPException

from spendscan.api.dependencies import SessionDep
from spendscan.auth import CurrentUser
from spendscan.db.repositories import FolderRepository

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("")
def list_folders(
    session: SessionDep,
    current_user: CurrentUser,
):
    repo = FolderRepository(session)

    return repo.list_folders(
        user_id=current_user.id,
    )


@router.post("")
def create_folder(
    payload: dict,
    session: SessionDep,
    current_user: CurrentUser,
):
    repo = FolderRepository(session)

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
):
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
):
    repo = FolderRepository(session)

    repo.remove_receipt(
        folder_id=folder_id,
        receipt_id=receipt_id,
    )

    return {"success": True}
    
@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    repo = FolderRepository(session)

    repo.delete_folder(
        folder_id=folder_id,
    )

    return {"success": True}