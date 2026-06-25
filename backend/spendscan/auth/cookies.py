"""Authentication and CSRF cookie helpers."""

from __future__ import annotations

import secrets

from starlette.responses import Response

from spendscan.config import Settings

CSRF_HEADER_NAME = "X-CSRF-Token"
"""HTTP request header that must carry the CSRF token on mutating requests."""

CSRF_COOKIE_NAME = "ss_csrf_token"
"""Name of the readable (non-HttpOnly) CSRF cookie sent to the browser."""

CSRF_COOKIE_PATH = "/"
"""Cookie path scope for the CSRF token; covers the entire origin."""


def set_auth_cookies(response: Response, *, access_token: str, settings: Settings) -> None:
    """Store the access token in an HttpOnly cookie and issue a CSRF token.

    Sets two cookies on *response*:

    * ``settings.auth_cookie_name`` — HttpOnly, scoped to ``settings.api_prefix``,
      carries the JWT.
    * ``CSRF_COOKIE_NAME`` — readable by JavaScript, scoped to ``/``,
      carries a random 32-byte URL-safe token for double-submit CSRF protection.

    Also sets ``Cache-Control: no-store`` to prevent caching of auth responses.

    Args:
        response: Starlette/FastAPI response object to attach cookies to.
        access_token: Signed JWT returned by :func:`~spendscan.auth.tokens.create_access_token`.
        settings: Application settings supplying cookie configuration.
    """
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
    """Expire the auth and CSRF cookies to log the user out.

    Deletes both cookies using the same ``path``, ``secure``, ``httponly``,
    and ``samesite`` attributes that were used when setting them, which is
    required for browsers to honour the deletion.

    Also sets ``Cache-Control: no-store`` to prevent caching of logout responses.

    Args:
        response: Starlette/FastAPI response object to clear cookies on.
        settings: Application settings supplying cookie configuration.
    """
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
