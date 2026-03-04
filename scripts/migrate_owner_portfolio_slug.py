"""
Add portfolio_slug column to owner_profiles.
Slugs are created on first use via GET /dashboard/owner/portfolio-link.
Run from project root: python scripts/migrate_owner_portfolio_slug.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from sqlalchemy import text

    try:
        from app.database import engine
    except Exception as e:
        print(f"Cannot get engine: {e}")
        sys.exit(1)

    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE owner_profiles ADD COLUMN IF NOT EXISTS portfolio_slug VARCHAR(32)"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_owner_profiles_portfolio_slug ON owner_profiles (portfolio_slug)"
            ))
            conn.commit()
            print("owner_profiles.portfolio_slug column and index: ok")
        except Exception as e:
            print(f"Error: {e}")
            raise
    print("Done.")


if __name__ == "__main__":
    main()
