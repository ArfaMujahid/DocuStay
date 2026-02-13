"""
Add revoked_at column to stays table (Kill Switch).
For a NEW database: not needed; app.models.stay.Stay already defines this (create_all creates it).
Run once on an EXISTING DB: python scripts/migrate_stays_revoked_at.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("stays")}
    if "revoked_at" in existing:
        print("  skip (exists): stays.revoked_at")
        print("Done.")
        return
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE stays ADD COLUMN "revoked_at" TIMESTAMP WITH TIME ZONE'))
        print("  added: stays.revoked_at")
    print("Done. stays table has revoked_at column.")


if __name__ == "__main__":
    main()
