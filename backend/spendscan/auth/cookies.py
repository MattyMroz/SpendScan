"""Authentication and CSRF cookie helpers."""

from __future__ import annotations

import secrets

from starlette.responses import Response

from spendscan.config import Settings

CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "ss_csrf_token"
CSRF_COOKIE_PATH = "/"


def set_auth_cookies(response: Response, *, access_token: str, settings: Settings) -> None:
    """Store the access token in an HttpOnly cookie and issue a CSRF token."""
    max_age = settings.jwt_expires_minutes * 60
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path=settings.api_prefix,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=secrets.token_urlsafe(32),
        max_age=max_age,
        httponly=False,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path=CSRF_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response, *, settings: Settings) -> None:
    """Expire authentication cookies using the same options they were created with."""
    response.headers["Cache-Control"] = "no-store"
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path=settings.api_prefix,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path=CSRF_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        httponly=False,
        samesite=settings.auth_cookie_samesite,
    )
