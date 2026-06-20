"""Authentication helpers: password hashing, JWT, FastAPI dependencies."""

from __future__ import annotations

from .cookies import CSRF_HEADER_NAME, clear_auth_cookies, set_auth_cookies
from .dependencies import CurrentUser, get_current_user
from .passwords import hash_password, verify_password
from .schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from .tokens import create_access_token, decode_access_token

__all__ = [
    "CSRF_HEADER_NAME",
    "AuthResponse",
    "CurrentUser",
    "LoginRequest",
    "RegisterRequest",
    "UserResponse",
    "clear_auth_cookies",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "hash_password",
    "set_auth_cookies",
    "verify_password",
]
