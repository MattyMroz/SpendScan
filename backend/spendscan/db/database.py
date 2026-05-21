from collections.abc import Generator

from sqlalchemy import Engine
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

from spendscan.config import Settings, get_settings


def create_database_engine(settings: Settings | None = None) -> Engine:
    """Create a SQLAlchemy engine for the configured database URL."""
    resolved_settings = settings or get_settings()
    database_url = resolved_settings.database_url_value
    connect_args: dict[str, int] = {}
    if make_url(database_url).drivername.startswith("postgresql"):
        connect_args["connect_timeout"] = 5
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


engine = create_database_engine()


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
