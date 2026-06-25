"""Folder persistence helpers.

Provides FolderRepository for managing user-defined receipt folders and
the many-to-many links between folders and receipts.
"""

from sqlmodel import Session, select

from spendscan.models import Folder, FolderReceipt


class FolderRepository:
    """Database access for folder CRUD and folder-receipt link management.

    Attributes:
        _session: Active SQLModel/SQLAlchemy session injected at construction.
    """

    def __init__(self, session: Session) -> None:
        """Initialise the repository with an active database session.

        Args:
            session: SQLModel session used for all database operations.
        """
        self._session = session

    def list_folders(self, *, user_id: int) -> list[Folder]:
        """Return all folders owned by a user, sorted by name.

        Args:
            user_id: Owner's primary key.

        Returns:
            List of Folder rows in ascending name order.
        """
        statement = select(Folder).where(Folder.user_id == user_id).order_by(Folder.name)
        return list(self._session.exec(statement).all())

    def create_folder(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None = None,
    ) -> Folder:
        """Insert a new folder and return the persisted row.

        Args:
            user_id: Owner's primary key.
            name: Display name for the folder.
            description: Optional free-text description.

        Returns:
            Refreshed Folder row with the auto-assigned id.
        """
        folder = Folder(
            user_id=user_id,
            name=name,
            description=description,
        )

        self._session.add(folder)
        self._session.commit()
        self._session.refresh(folder)

        return folder

    def assign_receipt(
        self,
        *,
        folder_id: int,
        receipt_id: int,
    ) -> FolderReceipt:
        """Link a receipt to a folder, returning the existing link if already present.

        Args:
            folder_id: Target folder's primary key.
            receipt_id: Receipt to assign.

        Returns:
            FolderReceipt link row (existing or newly created).
        """
        existing = self._session.exec(
            select(FolderReceipt).where(
                FolderReceipt.folder_id == folder_id,
                FolderReceipt.receipt_id == receipt_id,
            )
        ).first()

        if existing:
            return existing

        link = FolderReceipt(
            folder_id=folder_id,
            receipt_id=receipt_id,
        )

        self._session.add(link)
        self._session.commit()
        self._session.refresh(link)

        return link

    def get_receipt_folder_ids(
        self,
        receipt_id: int,
    ) -> list[int]:
        """Return the ids of all folders that contain a given receipt.

        Args:
            receipt_id: Receipt whose folder memberships to query.

        Returns:
            List of folder primary keys; empty when the receipt is in no folder.
        """
        statement = select(FolderReceipt.folder_id).where(FolderReceipt.receipt_id == receipt_id)

        return list(self._session.exec(statement).all())

    def remove_receipt(
        self,
        *,
        folder_id: int,
        receipt_id: int,
    ) -> None:
        """Remove the link between a folder and a receipt; no-op if absent.

        Args:
            folder_id: Folder to unlink from.
            receipt_id: Receipt to remove from the folder.
        """
        link = self._session.exec(
            select(FolderReceipt).where(
                FolderReceipt.folder_id == folder_id,
                FolderReceipt.receipt_id == receipt_id,
            )
        ).first()

        if link:
            self._session.delete(link)
            self._session.commit()

    def update_folder(
        self,
        *,
        folder_id: int,
        user_id: int | None,
        description: str | None = None,
    ) -> Folder | None:
        """Update a folder's description and return the refreshed row.

        Returns None when the folder does not exist or belongs to a
        different user (when user_id is provided).

        Args:
            folder_id: Primary key of the folder to update.
            user_id: Expected owner; pass None to skip ownership check.
            description: New description value (replaces the current one).

        Returns:
            Updated Folder row, or None if not found / unauthorised.
        """
        folder = self._session.get(Folder, folder_id)

        if folder is None:
            return None

        if user_id is not None and folder.user_id != user_id:
            return None

        folder.description = description

        self._session.add(folder)
        self._session.commit()
        self._session.refresh(folder)

        return folder

    def delete_folder(
        self,
        *,
        folder_id: int,
    ) -> None:
        """Delete a folder and all its receipt links; no-op if not found.

        Removes all FolderReceipt rows for the folder before deleting the
        Folder row itself, avoiding FK constraint violations.

        Args:
            folder_id: Primary key of the folder to delete.
        """
        links = self._session.exec(select(FolderReceipt).where(FolderReceipt.folder_id == folder_id)).all()

        for link in links:
            self._session.delete(link)

        folder = self._session.get(
            Folder,
            folder_id,
        )

        if folder:
            self._session.delete(folder)

        self._session.commit()
