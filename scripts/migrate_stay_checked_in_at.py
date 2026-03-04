"""
Add checked_in_at column to stays and backfill for existing active stays.
Occupancy and DMS now apply only after guest checks in; backfill treats existing
active stays (not checked out, not cancelled) as checked in at stay_start_date.
Run from project root: python scripts/migrate_stay_checked_in_at.py
"""
import os
import sys
from datetime import datetime, timezone, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import SessionLocal
    from app.models.stay import Stay
    from sqlalchemy import text

    engine = None
    try:
        from app.database import engine
    except Exception:
        pass
    if engine is not None:
        with engine.connect() as conn:
            try:
                # PostgreSQL; for SQLite use DATETIME if this fails
                conn.execute(text(
                    "ALTER TABLE stays ADD COLUMN checked_in_at TIMESTAMP WITH TIME ZONE"
                ))
                conn.commit()
                print("  stays.checked_in_at column: added")
            except Exception as e:
                err = str(e).lower()
                if "duplicate column" in err or "already exists" in err:
                    print("  stays.checked_in_at column: already exists")
                else:
                    try:
                        conn.rollback()
                        conn.execute(text(
                            "ALTER TABLE stays ADD COLUMN checked_in_at DATETIME"
                        ))
                        conn.commit()
                        print("  stays.checked_in_at column: added (SQLite)")
                    except Exception as e2:
                        if "duplicate column" in str(e2).lower() or "already exists" in str(e2).lower():
                            print("  stays.checked_in_at column: already exists")
                        else:
                            print(f"  stays.checked_in_at: {e2}")
                            raise

    db = SessionLocal()
    try:
        # Backfill: set checked_in_at = start of stay_start_date (UTC) for stays that are
        # not checked out and not cancelled, so existing "active" stays remain OCCUPIED.
        stays = db.query(Stay).filter(
            Stay.checked_out_at.is_(None),
            Stay.cancelled_at.is_(None),
        ).all()
        updated = 0
        for s in stays:
            if getattr(s, "checked_in_at", None) is not None:
                continue
            checked_in_at = datetime.combine(s.stay_start_date, time(0, 0, 0), tzinfo=timezone.utc)
            s.checked_in_at = checked_in_at
            db.add(s)
            updated += 1
        db.commit()
        print(f"  Backfilled checked_in_at for {updated} existing active stays.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
