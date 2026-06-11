"""User persistence."""

from __future__ import annotations

from sqlmodel import Session, col, select

from spendscan.models import User


class UserRepository:
    """Database access for users."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_user(self, *, username: str, email: str, password_hash: str) -> User:
        """Insert a new user and return the persisted row."""
        user = User(username=username, email=email, password_hash=password_hash)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        """Return the user matching the given email (case-insensitive) or None."""
        statement = select(User).where(col(User.email).ilike(email))
        return self._session.exec(statement).first()

    def get_by_username(self, username: str) -> User | None:
        """Return the user matching the given username (case-insensitive) or None."""
        statement = select(User).where(col(User.username).ilike(username))
        return self._session.exec(statement).first()

    def get_by_id(self, user_id: int) -> User | None:
        """Return the user with the given id or None."""
        return self._session.get(User, user_id)
