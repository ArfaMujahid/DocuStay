"""
Make any legacy audit_logs columns nullable if they are NOT in the current AuditLog model.
Older DB schemas may have entity_type, entity_id, action, etc. as NOT NULL; the app does not set them.
For a NEW database: not needed; schema matches model.
Run once on an EXISTING DB: python scripts/migrate_audit_logs_entity_type_nullable.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine
from app.models.audit_log import AuditLog

# Column names defined by current model (app won't INSERT these)
MODEL_COLUMNS = {c.name for c in AuditLog.__table__.columns}


def main():
    insp = inspect(engine)
    if "audit_logs" not in insp.get_table_names():
        print("  skip: audit_logs table does not exist")
        return
    existing = {c["name"]: c for c in insp.get_columns("audit_logs")}
    legacy_not_null = [name for name, c in existing.items() if name not in MODEL_COLUMNS and not c.get("nullable")]
    if not legacy_not_null:
        print("  no legacy NOT NULL columns to relax")
        print("Done.")
        return
    with engine.begin() as conn:
        for col_name in legacy_not_null:
            conn.execute(text(f'ALTER TABLE audit_logs ALTER COLUMN "{col_name}" DROP NOT NULL'))
            print(f"  updated: audit_logs.{col_name} is now nullable")
    print("Done.")


if __name__ == "__main__":
    main()
