"""FastAPI auth dependencies."""

from __future__ import annotations

import secrets
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from spendscan.config import Settings, get_settings
from spendscan.db import get_session
from spendscan.db.repositories.users import UserRepository
from spendscan.models import User

from .cookies import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from .tokens import decode_access_token

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
"""HTTP methods that do not mutate state and therefore skip CSRF validation."""


def get_current_user(
    request: Request,
    bearer_token: Annotated[str | None, Depends(_oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Resolve a user from an HttpOnly cookie or a backward-compatible Bearer token.

    Token resolution order: Bearer header first, then the HttpOnly auth cookie.
    For cookie-authenticated mutating requests (not in ``_SAFE_METHODS``) the
    double-submit CSRF check is enforced: the ``X-CSRF-Token`` header must
    match the ``ss_csrf_token`` cookie via a constant-time comparison.

    Args:
        request: Incoming FastAPI request used to read cookies and headers.
        bearer_token: Optional Bearer token extracted by the OAuth2 scheme.
        session: SQLModel database session injected by FastAPI.
        settings: Application settings supplying the cookie name and JWT config.

    Returns:
        Authenticated ``User`` model instance.

    Raises:
        HTTPException: 401 if no valid token is present or the JWT is invalid.
        HTTPException: 403 if the CSRF check fails on a mutating cookie-auth request.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    token = bearer_token or cookie_token
    if not token:
        raise credentials_error
    if bearer_token is None and request.method.upper() not in _SAFE_METHODS:
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token",
            )
    try:
        user_id = decode_access_token(token, settings=settings)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
