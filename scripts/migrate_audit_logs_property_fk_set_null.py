"""
Set audit_logs.property_id FK to ON DELETE SET NULL so property deletion works
after logging "Property deleted" (the log row keeps message/meta; property_id becomes null).
For a NEW database: not needed; AuditLog model already has ondelete="SET NULL".
Run once on an EXISTING DB: python scripts/migrate_audit_logs_property_fk_set_null.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    if "audit_logs" not in insp.get_table_names():
        print("  skip: audit_logs table does not exist")
        return
    with engine.begin() as conn:
        r = conn.execute(text("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'audit_logs'::regclass AND contype = 'f' AND conname LIKE '%property%'
        """))
        names = [row[0] for row in r]
    if not names:
        print("  skip: no property_id FK found on audit_logs")
        return
    fk_name = names[0]
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS "{fk_name}"'))
        print(f"  dropped: {fk_name}")
        conn.execute(text(
            'ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_property_id_fkey '
            'FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL'
        ))
        print("  added: audit_logs_property_id_fkey ON DELETE SET NULL")
    print("Done.")


if __name__ == "__main__":
    main()
