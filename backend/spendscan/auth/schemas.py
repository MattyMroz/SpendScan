"""Auth request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user representation."""

    id: int
    username: str
    email: EmailStr
    created_at: datetime | None


class AuthResponse(BaseModel):
    """Successful browser authentication response without exposing the JWT."""

    expires_in: int
    user: UserResponse
