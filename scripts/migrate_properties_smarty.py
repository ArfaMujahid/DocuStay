"""Add Smarty address standardization columns to properties.
For a NEW database: not needed; models define these.
Run once on an EXISTING DB: python scripts/migrate_properties_smarty.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


_COLUMNS = [
    ("smarty_delivery_line_1", "VARCHAR(64)"),
    ("smarty_city_name", "VARCHAR(64)"),
    ("smarty_state_abbreviation", "VARCHAR(2)"),
    ("smarty_zipcode", "VARCHAR(5)"),
    ("smarty_plus4_code", "VARCHAR(4)"),
    ("smarty_latitude", "DOUBLE PRECISION"),
    ("smarty_longitude", "DOUBLE PRECISION"),
]


def main():
    insp = inspect(engine)
    if "properties" not in insp.get_table_names():
        print("  skip: properties table does not exist")
        return
    cols = {c["name"] for c in insp.get_columns("properties")}
    with engine.begin() as conn:
        for name, dtype in _COLUMNS:
            if name in cols:
                print(f"  skip (exists): properties.{name}")
            else:
                conn.execute(text(f"ALTER TABLE properties ADD COLUMN {name} {dtype}"))
                print(f"  added: properties.{name}")
    print("Done.")


if __name__ == "__main__":
    main()
