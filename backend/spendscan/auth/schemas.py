"""Auth request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register.

    Attributes:
        username: Desired username, 3-50 characters.
        email: Valid email address used for login.
        password: Plaintext password, 8-128 characters.
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Payload for POST /auth/login.

    Attributes:
        email: Registered email address.
        password: Plaintext password to verify.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user representation returned in auth responses.

    Attributes:
        id: Database primary key.
        username: Display name.
        email: Registered email address.
        created_at: UTC timestamp of account creation, or None if unavailable.
    """

    id: int
    username: str
    email: EmailStr
    created_at: datetime | None


class AuthResponse(BaseModel):
    """Successful browser authentication response without exposing the JWT.

    The JWT itself is delivered via an HttpOnly cookie; this body carries
    only the metadata needed by the client.

    Attributes:
        expires_in: Token lifetime in seconds.
        user: Public profile of the authenticated user.
    """

    expires_in: int
    user: UserResponse
