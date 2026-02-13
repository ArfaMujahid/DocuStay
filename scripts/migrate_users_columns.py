"""
Add missing columns to users table to match app.models.user.User.
For a NEW database: not needed; User model already defines these (create_all creates them).
Run once on an EXISTING DB: python scripts/migrate_users_columns.py (from project root)
"""
import os
import sys

# Project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine

# Columns that User model expects: (name, full SQL type for PostgreSQL)
COLUMNS = [
    ("full_name", "VARCHAR(255)"),
    ("phone", "VARCHAR(50)"),
    ("state", "VARCHAR(50)"),
    ("city", "VARCHAR(100)"),
    ("country", "VARCHAR(50)"),
    ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
    ("updated_at", "TIMESTAMP WITH TIME ZONE"),
    ("email_verified", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("email_verification_code", "VARCHAR(10)"),
    ("email_verification_expires_at", "TIMESTAMP WITH TIME ZONE"),
]


def main():
    from sqlalchemy import inspect
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("users")}
    with engine.begin() as conn:
        for name, sql_type in COLUMNS:
            if name in existing:
                print(f"  skip (exists): users.{name}")
                continue
            stmt = f'ALTER TABLE users ADD COLUMN "{name}" {sql_type}'
            conn.execute(text(stmt))
            print(f"  added: users.{name}")
        # Grandfather existing users as email_verified so they can still log in
        if "email_verified" not in existing:
            conn.execute(text("UPDATE users SET email_verified = TRUE WHERE email_verified IS NOT TRUE"))
            print("  set email_verified = TRUE for existing users")
    print("Done. users table now matches the model.")


if __name__ == "__main__":
    main()
