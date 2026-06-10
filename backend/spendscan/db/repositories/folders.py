from sqlmodel import Session, select

from spendscan.models import Folder, FolderReceipt


class FolderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_folders(self, *, user_id: int) -> list[Folder]:
        statement = (
            select(Folder)
            .where(Folder.user_id == user_id)
            .order_by(Folder.name)
        )
        return list(self._session.exec(statement).all())

    def create_folder(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None = None,
    ) -> Folder:
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
        statement = (
            select(FolderReceipt.folder_id)
            .where(FolderReceipt.receipt_id == receipt_id)
        )

        return list(self._session.exec(statement).all())

    def remove_receipt(
        self,
        *,
        folder_id: int,
        receipt_id: int,
    ) -> None:
        link = self._session.exec(
            select(FolderReceipt).where(
                FolderReceipt.folder_id == folder_id,
                FolderReceipt.receipt_id == receipt_id,
            )
        ).first()

        if link:
            self._session.delete(link)
            self._session.commit()

    def delete_folder(
        self,
        *,
        folder_id: int,
    ) -> None:
        links = self._session.exec(
            select(FolderReceipt).where(
                FolderReceipt.folder_id == folder_id
            )
        ).all()

        for link in links:
            self._session.delete(link)

        folder = self._session.get(
            Folder,
            folder_id,
        )

        if folder:
            self._session.delete(folder)

        self._session.commit()