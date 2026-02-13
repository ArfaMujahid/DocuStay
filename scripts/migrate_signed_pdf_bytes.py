"""
Add signed_pdf_bytes column to owner_poa_signatures and agreement_signatures.
Run once on an EXISTING DB: python scripts/migrate_signed_pdf_bytes.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    dialect = engine.dialect.name
    blob_type = "BYTEA" if dialect == "postgresql" else "BLOB"
    with engine.begin() as conn:
        for table, col in [("owner_poa_signatures", "signed_pdf_bytes"), ("agreement_signatures", "signed_pdf_bytes")]:
            if table not in insp.get_table_names():
                print(f"  skip (table missing): {table}")
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if col in cols:
                print(f"  skip (exists): {table}.{col}")
            else:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {blob_type}'))
                print(f"  added: {table}.{col}")
    print("Done.")


if __name__ == "__main__":
    main()
