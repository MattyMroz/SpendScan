from __future__ import annotations

from pydantic import SecretStr
from sqlmodel import Session

from spendscan.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from spendscan.config import Settings
from spendscan.db.repositories import UserRepository


def _settings() -> Settings:
    return Settings(jwt_secret=SecretStr("test-secret"))


def test_hash_and_verify_password_roundtrip() -> None:
    hashed = hash_password("S3cret!Pass")
    assert hashed != "S3cret!Pass"
    assert verify_password("S3cret!Pass", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_token_roundtrip() -> None:
    settings = _settings()
    token = create_access_token(user_id=42, settings=settings)
    assert decode_access_token(token, settings=settings) == 42


def test_register_endpoint_creates_user_and_returns_token(api_client) -> None:
    response = api_client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Password123!"},
    )
    assert response.status_code == 201, response.json()
    payload = response.json()
    assert payload["token_type"] == "bearer"  # noqa: S105
    assert payload["access_token"]


def test_login_endpoint_returns_token_for_valid_credentials(db_session: Session, api_client) -> None:
    UserRepository(db_session).create_user(
        username="bob",
        email="bob@example.com",
        password_hash=hash_password("Password123!"),
    )
    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["access_token"]


def test_login_endpoint_rejects_bad_password(db_session: Session, api_client) -> None:
    UserRepository(db_session).create_user(
        username="carol",
        email="carol@example.com",
        password_hash=hash_password("Password123!"),
    )
    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "WrongPass!!"},
    )
    assert response.status_code == 401


def test_me_endpoint_returns_authenticated_user(api_client) -> None:
    response = api_client.get("/api/v1/auth/me")
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["username"] == "tester"
    assert payload["email"] == "tester@example.com"
    assert payload["coins"] == 0


def test_protected_endpoint_rejects_missing_token(api_client) -> None:
    response = api_client.get("/api/v1/receipts", headers={"Authorization": ""})
    assert response.status_code == 401
