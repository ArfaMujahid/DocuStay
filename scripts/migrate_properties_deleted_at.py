"""
Add deleted_at column to properties table (soft delete).
For a NEW database: not needed; app.models.owner.Property already defines it.
Run once on an EXISTING DB: python scripts/migrate_properties_deleted_at.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("properties")}
    if "deleted_at" in existing:
        print("  skip (exists): properties.deleted_at")
    else:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE properties ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE'))
        print("  added: properties.deleted_at")
    print("Done.")


if __name__ == "__main__":
    main()
