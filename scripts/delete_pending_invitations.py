"""
Delete all invitations in pending state from the database.
Run once: python scripts/delete_pending_invitations.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.invitation import Invitation


def main():
    db = SessionLocal()
    try:
        deleted = db.query(Invitation).filter(Invitation.status == "pending").delete()
        db.commit()
        print(f"Deleted {deleted} pending invitation(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
