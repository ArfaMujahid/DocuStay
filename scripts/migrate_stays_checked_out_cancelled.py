"""
Add checked_out_at and cancelled_at columns to stays table.
For a NEW database: not needed; app.models.stay.Stay already defines these (create_all creates them).
Run once on an EXISTING DB: python scripts/migrate_stays_checked_out_cancelled.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("stays")}
    with engine.begin() as conn:
        if "checked_out_at" not in existing:
            conn.execute(text('ALTER TABLE stays ADD COLUMN "checked_out_at" TIMESTAMP WITH TIME ZONE'))
            print("  added: stays.checked_out_at")
        else:
            print("  skip (exists): stays.checked_out_at")
        if "cancelled_at" not in existing:
            conn.execute(text('ALTER TABLE stays ADD COLUMN "cancelled_at" TIMESTAMP WITH TIME ZONE'))
            print("  added: stays.cancelled_at")
        else:
            print("  skip (exists): stays.cancelled_at")
    print("Done.")


if __name__ == "__main__":
    main()
