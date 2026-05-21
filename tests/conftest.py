from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from spendscan.api.app import create_app
from spendscan.config import Settings, get_settings
from spendscan.db.database import get_session
from spendscan.models import Category, Receipt, ReceiptImage, ReceiptItem, User

_MODEL_IMPORTS = (Category, Receipt, ReceiptImage, ReceiptItem, User)


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def api_client(db_session: Session, tmp_path: Path) -> Generator[TestClient]:
    settings = Settings(database_url=SecretStr("sqlite://"), upload_dir=tmp_path / "uploads")
    app = create_app(settings)

    def override_get_session() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
