"""
Create audit_logs table (append-only audit trail) if it does not exist.
For a NEW database: not needed; app.models.audit_log.AuditLog is in create_all (startup creates it).
Run once on an EXISTING DB: python scripts/migrate_audit_logs.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from app.database import engine, Base
from app.models.audit_log import AuditLog


def main():
    insp = inspect(engine)
    if "audit_logs" in insp.get_table_names():
        print("  skip (exists): audit_logs")
    else:
        AuditLog.__table__.create(engine)
        print("  created: audit_logs")
    print("Done.")


if __name__ == "__main__":
    main()
