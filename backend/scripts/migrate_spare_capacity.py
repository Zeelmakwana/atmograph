from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text

from app.core.database import engine


TABLE_NAME = "sc_supply_allocations"
COLUMN_NAME = "spare_capacity_units"


def migrate() -> None:
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if TABLE_NAME not in tables:
        print(
            f"[INFO] Table '{TABLE_NAME}' does not exist."
        )
        print(
            "[INFO] No ALTER TABLE migration is required."
        )
        return

    columns = {
        column["name"]
        for column in inspector.get_columns(
            TABLE_NAME
        )
    }

    if COLUMN_NAME in columns:
        print(
            f"[OK] '{COLUMN_NAME}' already exists "
            f"in '{TABLE_NAME}'."
        )
        return

    dialect = engine.dialect.name

    print(
        f"[INFO] Database dialect: {dialect}"
    )

    if dialect == "sqlite":

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE sc_supply_allocations
                    ADD COLUMN spare_capacity_units
                    FLOAT NOT NULL DEFAULT 0.0
                    """
                )
            )

    elif dialect == "postgresql":

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE sc_supply_allocations
                    ADD COLUMN spare_capacity_units
                    DOUBLE PRECISION NOT NULL
                    DEFAULT 0.0
                    """
                )
            )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )

    print(
        "[OK] Added 'spare_capacity_units' "
        "to 'sc_supply_allocations'."
    )


if __name__ == "__main__":
    migrate()