"""
Clear usat_token_released_at for all stays so no guest sees the USAT token until the owner
explicitly releases it to them again (via My Properties > Release/Manage > select guests).

Run once if guests are seeing the token before the owner released it to them:
  python scripts/clear_usat_token_released_at.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine


def main():
    with engine.begin() as conn:
        r = conn.execute(text("UPDATE stays SET usat_token_released_at = NULL WHERE usat_token_released_at IS NOT NULL"))
        count = r.rowcount
    print(f"Cleared usat_token_released_at for {count} stay(s). Guests will no longer see the token until the owner uses Release/Manage to select them.")
    print("Done.")


if __name__ == "__main__":
    main()
