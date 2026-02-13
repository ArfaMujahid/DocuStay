"""
Add dropbox_sign_request_id to agreement_signatures.
For a NEW database: not needed; app.models.agreement_signature.AgreementSignature already defines it.
Run once on an EXISTING DB: python scripts/migrate_agreement_signature_dropbox.py (from project root)
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text, inspect
from app.database import engine

def main():
    insp = inspect(engine)
    existing = {c["name"] for c in insp.get_columns("agreement_signatures")}
    if "dropbox_sign_request_id" in existing:
        print("  skip: agreement_signatures.dropbox_sign_request_id exists")
        return
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE agreement_signatures ADD COLUMN dropbox_sign_request_id VARCHAR(64)'))
    print("  added: agreement_signatures.dropbox_sign_request_id")

if __name__ == "__main__":
    main()
