"""
Add shield_mode_enabled column to properties table.
Run once on an EXISTING DB: python scripts/migrate_properties_shield_mode.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("properties")}
    with engine.begin() as conn:
        if "shield_mode_enabled" not in cols:
            conn.execute(text('ALTER TABLE properties ADD COLUMN "shield_mode_enabled" INTEGER NOT NULL DEFAULT 0'))
            print("  added: properties.shield_mode_enabled")
        else:
            print("  skip (exists): properties.shield_mode_enabled")
    print("Done.")


if __name__ == "__main__":
    main()
