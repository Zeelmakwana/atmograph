from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

# Current file:
# backend/scripts/verify_supply_chain_schema.py
#
# parents[0] = backend/scripts
# parents[1] = backend
PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# APP IMPORTS
# ============================================================

from sqlalchemy import inspect

from app.core.database import engine


# ============================================================
# REQUIRED SCHEMA
# ============================================================

REQUIRED_COLUMNS = {
    "sc_supply_allocations": [
        "supplier_id",
        "component_id",
        "plant_id",
        "allocation_pct",
        "capacity_units",
        "spare_capacity_units",
        "lead_time_days",
        "criticality",
    ],
    "sc_dependencies": [
        "dependency_id",
        "source_type",
        "source_id",
        "target_type",
        "target_id",
        "dependency_type",
        "required_quantity",
        "criticality",
    ],
}


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    inspector = inspect(
        engine
    )

    print(
        f"[INFO] Project root: "
        f"{PROJECT_ROOT}"
    )

    print(
        f"[INFO] Database dialect: "
        f"{engine.dialect.name}"
    )

    failed = False

    for (
        table,
        required_columns,
    ) in REQUIRED_COLUMNS.items():

        print()
        print(
            f"[TABLE] {table}"
        )

        if not inspector.has_table(
            table
        ):
            print(
                f"[ERROR] Missing table: "
                f"{table}"
            )

            failed = True
            continue

        actual_columns = {
            column["name"]
            for column in inspector.get_columns(
                table
            )
        }

        for column in required_columns:

            if column in actual_columns:

                print(
                    f"[OK] {column}"
                )

            else:

                print(
                    f"[ERROR] Missing column: "
                    f"{column}"
                )

                failed = True

    print()

    if failed:

        print(
            "[FAIL] Supply-chain schema "
            "verification failed."
        )

        return 1

    print(
        "[OK] Supply-chain schema "
        "verification passed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )