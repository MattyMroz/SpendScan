"""Authentication endpoints: register, login, current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from spendscan.auth import (
    AuthResponse,
    CurrentUser,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    clear_auth_cookies,
    create_access_token,
    hash_password,
    set_auth_cookies,
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


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    """Register a new user and store a JWT in an HttpOnly cookie."""
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
    set_auth_cookies(response, access_token=token, settings=settings)
    return AuthResponse(
        expires_in=settings.jwt_expires_minutes * 60,
        user=_to_user_response(user.id, user.username, user.email, user.created_at),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    """Verify credentials and store a JWT in an HttpOnly cookie."""
    user = UserRepository(session).get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User id missing")
    token = create_access_token(user_id=user.id, settings=settings)
    set_auth_cookies(response, access_token=token, settings=settings)
    return AuthResponse(
        expires_in=settings.jwt_expires_minutes * 60,
        user=_to_user_response(user.id, user.username, user.email, user.created_at),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: CurrentUser,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Expire the browser authentication and CSRF cookies."""
    clear_auth_cookies(response, settings=settings)


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
