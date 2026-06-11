"""Drop and recreate all SpendScan tables from current SQLModel metadata."""

from __future__ import annotations

import sys

from sqlmodel import SQLModel

from spendscan.db.database import create_database_engine
from spendscan.models import db_models as _db_models  # noqa: F401  (register tables)


def main() -> int:
    engine = create_database_engine()
    print(f"Resetting schema on {engine.url}")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print(f"Created {len(SQLModel.metadata.tables)} tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
