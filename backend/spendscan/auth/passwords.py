"""Password hashing helpers using bcrypt."""

from __future__ import annotations

from passlib.context import CryptContext

_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    hashed: str = _context.hash(password)
    return hashed


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    ok: bool = _context.verify(password, password_hash)
    return ok
