"""
Add password_reset_token and password_reset_expires_at to users table if they do not exist.
For existing databases created before one-time reset links were added.
Run from project root: python scripts/migrate_password_reset_columns.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        for col, typ in [
            ("password_reset_token", "VARCHAR(255)"),
            ("password_reset_expires_at", "TIMESTAMP WITH TIME ZONE"),
        ]:
            try:
                conn.execute(text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}"
                ))
                print(f"  users.{col}: ok")
            except Exception as e:
                print(f"  users.{col}: {e}")
        conn.commit()
    print("Done.")


if __name__ == "__main__":
    main()
