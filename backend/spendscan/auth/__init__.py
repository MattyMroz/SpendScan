"""Authentication helpers: password hashing, JWT, FastAPI dependencies."""

from __future__ import annotations

from .dependencies import CurrentUser, get_current_user
from .passwords import hash_password, verify_password
from .schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .tokens import create_access_token, decode_access_token

__all__ = [
    "CurrentUser",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "hash_password",
    "verify_password",
]
