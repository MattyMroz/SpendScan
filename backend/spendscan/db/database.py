from collections.abc import Generator
from os import getenv

from sqlmodel import Session, create_engine

DATABASE_URL = getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/spendscan",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
