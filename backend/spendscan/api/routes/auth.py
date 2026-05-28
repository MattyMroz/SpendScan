"""Authentication endpoints: register, login, current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from spendscan.auth import (
    CurrentUser,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    create_access_token,
    hash_password,
    verify_password,
)
from spendscan.config import Settings, get_settings
from spendscan.db import get_session
from spendscan.db.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user_id: int, username: str, email: str, created_at: object) -> UserResponse:
    return UserResponse(
        id=user_id,
        username=username,
        email=email,
        created_at=created_at,  # type: ignore[arg-type]
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Register a new user and return a JWT access token."""
    repo = UserRepository(session)
    if repo.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if repo.get_by_username(payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    user = repo.create_user(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id not assigned")
    token = create_access_token(user_id=user.id, settings=settings)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expires_minutes * 60)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Verify credentials and return a JWT access token."""
    user = UserRepository(session).get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    token = create_access_token(user_id=user.id, settings=settings)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expires_minutes * 60)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    """Return profile of the authenticated user."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    return _to_user_response(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
    )
