"""Check if an owner with the given email exists in the database."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole

EMAIL = "arfamujahid12@gmail.com"


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == EMAIL.strip().lower(),
            User.role == UserRole.owner,
        ).first()
        if user:
            print(f"YES - Owner exists: id={user.id}, email={user.email}")
        else:
            print(f"NO - No owner found with email: {EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
