from collections.abc import Generator
from os import getenv

from sqlmodel import Session, create_engine

DATABASE_URL = getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/spendscan",
)

engine = create_engine(DATABASE_URL)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
