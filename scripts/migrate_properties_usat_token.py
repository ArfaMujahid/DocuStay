"""
Add USAT token columns to properties table (staged tokens).
For a NEW database: not needed; app.models.owner.Property already defines these (create_all creates them).
Run once on an EXISTING DB: python scripts/migrate_properties_usat_token.py (from project root)
"""
import os
import sys
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine

COLUMNS = [
    ("usat_token", "VARCHAR(64) UNIQUE"),
    ("usat_token_state", "VARCHAR(20) NOT NULL DEFAULT 'staged'"),
    ("usat_token_released_at", "TIMESTAMP WITH TIME ZONE"),
]


def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("properties")}
    with engine.begin() as conn:
        for name, sql_type in COLUMNS:
            if name in existing:
                print(f"  skip (exists): properties.{name}")
                continue
            stmt = f'ALTER TABLE properties ADD COLUMN "{name}" {sql_type}'
            conn.execute(text(stmt))
            print(f"  added: properties.{name}")
        # Backfill usat_token for rows that have none
        result = conn.execute(text("SELECT id FROM properties WHERE usat_token IS NULL"))
        ids = [row[0] for row in result]
        for pid in ids:
            token = "USAT-" + secrets.token_hex(12).upper()
            conn.execute(
                text("UPDATE properties SET usat_token = :t, usat_token_state = 'staged' WHERE id = :id"),
                {"t": token, "id": pid},
            )
            print(f"  backfilled token for property id={pid}")
    print("Done. properties table has USAT token columns.")


if __name__ == "__main__":
    main()
