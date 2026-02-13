"""
Create pending_registrations table (signup data until email verification).
For a NEW database: not needed; app.models.pending_registration.PendingRegistration is in create_all.
Run once on an EXISTING DB: python scripts/migrate_pending_registrations.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from app.database import engine, Base
from app.models.pending_registration import PendingRegistration


def main():
    insp = inspect(engine)
    if "pending_registrations" in insp.get_table_names():
        print("  skip (exists): pending_registrations")
    else:
        PendingRegistration.__table__.create(engine)
        print("  created: pending_registrations")
    print("Done.")


if __name__ == "__main__":
    main()
