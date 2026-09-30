from __future__ import annotations

import sys
from pathlib import Path

# ============================================================
# BOOTSTRAP BACKEND IMPORT PATH
# ============================================================

# File:
# backend/scripts/migrate_required_quantity.py
#
# parents[1] = backend
BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# APPLICATION IMPORT
# ============================================================

from sqlalchemy import inspect, text

from app.core.database import engine


# ============================================================
# CONFIGURATION
# ============================================================

TABLE_NAME = "sc_dependencies"
COLUMN_NAME = "required_quantity"


# ============================================================
# MIGRATION
# ============================================================

def migrate() -> None:
    """
    Add required_quantity to sc_dependencies if it does not
    already exist.

    Existing dependency rows receive:
        required_quantity = 1.0

    This keeps all existing AtmoGraph data backward compatible.
    """

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    # --------------------------------------------------------
    # Table does not exist
    # --------------------------------------------------------

    if TABLE_NAME not in tables:
        print(
            f"[INFO] Table '{TABLE_NAME}' does not exist."
        )
        print(
            "[INFO] No ALTER TABLE migration is required."
        )
        return

    # --------------------------------------------------------
    # Check existing columns
    # --------------------------------------------------------

    columns = {
        column["name"]
        for column in inspector.get_columns(
            TABLE_NAME
        )
    }

    if COLUMN_NAME in columns:
        print(
            f"[OK] '{COLUMN_NAME}' already exists in "
            f"'{TABLE_NAME}'."
        )
        return

    # --------------------------------------------------------
    # Database dialect
    # --------------------------------------------------------

    dialect = engine.dialect.name

    print(
        f"[INFO] Database dialect: {dialect}"
    )

    # --------------------------------------------------------
    # SQLite
    # --------------------------------------------------------

    if dialect == "sqlite":

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE sc_dependencies
                    ADD COLUMN required_quantity
                    FLOAT NOT NULL DEFAULT 1.0
                    """
                )
            )

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    elif dialect == "postgresql":

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE sc_dependencies
                    ADD COLUMN required_quantity
                    DOUBLE PRECISION NOT NULL
                    DEFAULT 1.0
                    """
                )
            )

    # --------------------------------------------------------
    # Unsupported database
    # --------------------------------------------------------

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )

    print(
        f"[OK] Added '{COLUMN_NAME}' to "
        f"'{TABLE_NAME}' with default 1.0."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    migrate()