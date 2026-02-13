"""
Create owner_poa_signatures table (Master POA signed at owner signup).
For a NEW database: not needed; app.models.owner_poa_signature.OwnerPOASignature is in create_all.
Run once on an EXISTING DB: python scripts/migrate_owner_poa_signatures.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from app.database import engine, Base
from app.models.owner_poa_signature import OwnerPOASignature


def main():
    insp = inspect(engine)
    if "owner_poa_signatures" in insp.get_table_names():
        print("  skip (exists): owner_poa_signatures")
    else:
        OwnerPOASignature.__table__.create(engine)
        print("  created: owner_poa_signatures")
    print("Done.")


if __name__ == "__main__":
    main()
