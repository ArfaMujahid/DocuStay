"""
Add vacant-unit monitoring columns to properties.
Run from project root: python scripts/migrate_vacant_monitoring_columns.py
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

    columns = [
        ("vacant_monitoring_enabled", "INTEGER NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0"),
        ("vacant_monitoring_last_prompted_at", "TIMESTAMP WITH TIME ZONE", "DATETIME"),
        ("vacant_monitoring_response_due_at", "TIMESTAMP WITH TIME ZONE", "DATETIME"),
        ("vacant_monitoring_confirmed_at", "TIMESTAMP WITH TIME ZONE", "DATETIME"),
    ]
    with engine.connect() as conn:
        for col_name, pg_type, sqlite_type in columns:
            try:
                conn.execute(text(
                    f"ALTER TABLE properties ADD COLUMN IF NOT EXISTS {col_name} {pg_type}"
                ))
                conn.commit()
                print(f"properties.{col_name}: ok")
            except Exception as e:
                err = str(e).lower()
                if "already exists" in err or "duplicate" in err:
                    print(f"properties.{col_name}: already exists")
                else:
                    try:
                        conn.rollback()
                        conn.execute(text(f"ALTER TABLE properties ADD COLUMN {col_name} {sqlite_type}"))
                        conn.commit()
                        print(f"properties.{col_name}: ok (SQLite)")
                    except Exception as e2:
                        if "duplicate column" in str(e2).lower() or "already exists" in str(e2).lower():
                            print(f"properties.{col_name}: already exists")
                        else:
                            print(f"Error adding {col_name}: {e2}")
                            raise
    print("Done.")


if __name__ == "__main__":
    main()
