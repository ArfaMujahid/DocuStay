"""Standalone script to create DB tables and seed region rules (Module D)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.seed import seed_region_rules

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_region_rules(db)
        print("Region rules seeded: NYC, FL, CA, TX.")
    finally:
        db.close()
