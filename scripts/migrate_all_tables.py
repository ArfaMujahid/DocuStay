"""
Best-effort schema sync for all SQLAlchemy models.

- Creates missing tables via Base.metadata.create_all()
- Adds missing columns to existing tables (from current models)

For a NEW database: not needed; app startup already runs create_all() with all models.
Run on an EXISTING DB to add any columns/tables that were added to models after the DB was created:
  python scripts/migrate_all_tables.py
"""
import os
import sys
from typing import Optional

# Project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.schema import DefaultClause  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app import models  # noqa: F401,E402


def _compile_type(col) -> str:
    return col.type.compile(dialect=engine.dialect)


def _compile_default(col) -> Optional[str]:
    if col.server_default is None:
        return None
    if isinstance(col.server_default, DefaultClause):
        arg = col.server_default.arg
        if arg is None:
            return None
        return str(arg.compile(dialect=engine.dialect))
    return None


def main():
    # Ensure tables/enums exist
    Base.metadata.create_all(bind=engine)

    insp = inspect(engine)
    table_names = set(insp.get_table_names())
    warnings = []

    with engine.begin() as conn:
        for table in Base.metadata.tables.values():
            if table.name not in table_names:
                # create_all should have created it; skip to avoid double-handling
                continue
            existing_cols = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing_cols:
                    continue
                col_type = _compile_type(col)
                default_sql = _compile_default(col)

                # Be safe with NOT NULL additions on existing rows.
                not_null = (not col.nullable) and default_sql is not None
                if (not col.nullable) and default_sql is None:
                    warnings.append(
                        f"{table.name}.{col.name} is NOT NULL in model "
                        "but added as NULL (no server default)."
                    )

                parts = [
                    f'ALTER TABLE {table.name} ADD COLUMN "{col.name}" {col_type}'
                ]
                if default_sql:
                    parts.append(f"DEFAULT {default_sql}")
                if not_null:
                    parts.append("NOT NULL")
                stmt = " ".join(parts)
                conn.execute(text(stmt))
                print(f"  added: {table.name}.{col.name}")

    print("Done. Checked all tables for missing columns.")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f" - {w}")


if __name__ == "__main__":
    main()
