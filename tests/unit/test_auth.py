from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlmodel import Session
from starlette.responses import Response

from spendscan.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    set_auth_cookies,
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


def test_secure_cookie_flag_is_enabled_by_production_setting() -> None:
    response = Response()
    settings = Settings(
        jwt_secret=SecretStr("test-secret-at-least-32-bytes-long"),
        auth_cookie_secure=True,
    )

    set_auth_cookies(response, access_token=create_access_token(user_id=1, settings=settings), settings=settings)

    set_cookie_headers = response.headers.getlist("set-cookie")
    assert set_cookie_headers
    assert all("Secure" in header for header in set_cookie_headers)


def test_register_endpoint_creates_user_and_sets_auth_cookies(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Password123!"},
    )
    assert response.status_code == 201, response.json()
    payload = response.json()
    assert "access_token" not in payload
    assert payload["user"]["username"] == "alice"
    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie = next(header for header in set_cookie_headers if header.startswith("ss_access_token="))
    assert "HttpOnly" in access_cookie
    assert "SameSite=lax" in access_cookie
    assert any(header.startswith("ss_csrf_token=") for header in set_cookie_headers)


def test_login_endpoint_sets_cookie_for_valid_credentials(db_session: Session, api_client: TestClient) -> None:
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
    assert "access_token" not in response.json()
    assert response.json()["user"]["username"] == "bob"
    cookie_me = api_client.get("/api/v1/auth/me", headers={"Authorization": ""})
    assert cookie_me.status_code == 200
    assert cookie_me.json()["username"] == "bob"


def test_cookie_authenticated_mutation_requires_csrf_token(db_session: Session, api_client: TestClient) -> None:
    UserRepository(db_session).create_user(
        username="dave",
        email="dave@example.com",
        password_hash=hash_password("Password123!"),
    )
    login_response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200

    missing_csrf = api_client.post("/api/v1/auth/logout", headers={"Authorization": ""})
    assert missing_csrf.status_code == 403

    csrf_token = api_client.cookies.get("ss_csrf_token")
    assert csrf_token
    logout_response = api_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "", "X-CSRF-Token": csrf_token},
    )
    assert logout_response.status_code == 204


def test_login_endpoint_rejects_bad_password(db_session: Session, api_client: TestClient) -> None:
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


def test_me_endpoint_returns_authenticated_user(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/auth/me")
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["username"] == "tester"
    assert payload["email"] == "tester@example.com"
    assert "coins" not in payload


def test_protected_endpoint_rejects_missing_token(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/receipts", headers={"Authorization": ""})
    assert response.status_code == 401
