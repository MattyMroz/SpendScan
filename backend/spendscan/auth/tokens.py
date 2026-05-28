"""JWT access token encode/decode."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from spendscan.config import Settings


def create_access_token(*, user_id: int, settings: Settings) -> str:
    """Issue a signed JWT for the given user id."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_value, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, *, settings: Settings) -> int:
    """Decode a JWT and return the user id; raises jwt.PyJWTError on failure."""
    payload = jwt.decode(token, settings.jwt_secret_value, algorithms=[settings.jwt_algorithm])
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        msg = "Invalid token subject"
        raise jwt.InvalidTokenError(msg)
    return int(sub)
