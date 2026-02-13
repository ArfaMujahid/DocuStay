"""
Add usat_token_released_at column to stays table (per-stay token release).
Only stays with this set will show the USAT token to the guest. Owner chooses which guest(s)
when releasing via the Release/Manage modal.
Run once on an EXISTING DB: python scripts/migrate_stays_usat_token_released_at.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("stays")}
    if "usat_token_released_at" in existing:
        print("  skip (exists): stays.usat_token_released_at")
        print("Done.")
        return
    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE stays ADD COLUMN "usat_token_released_at" TIMESTAMP WITH TIME ZONE'))
        print("  added: stays.usat_token_released_at")
    except Exception as e:
        if "already exists" in str(e).lower() or "42701" in str(e):
            print("  skip (exists): stays.usat_token_released_at")
        else:
            raise
    print("Done. Use Release/Manage on the dashboard to choose which guest(s) can see the token.")


if __name__ == "__main__":
    main()
