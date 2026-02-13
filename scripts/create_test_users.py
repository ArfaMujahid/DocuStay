"""
Create a test owner and a test guest user (no email verification required).
Use when verification emails are not configured so you can log in and test the app.

Run from project root:
  python scripts/create_test_users.py

Credentials are printed at the end. Use Owner Login for the owner, Guest Login for the guest.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.owner import OwnerProfile
from app.models.guest import GuestProfile
from app.services.auth import get_password_hash

# Default credentials (change if you want)
OWNER_EMAIL = "owner@docustay.demo"
OWNER_PASSWORD = "Password123!"
OWNER_FULL_NAME = "Test Owner"

GUEST_EMAIL = "guest@docustay.demo"
GUEST_PASSWORD = "Password123!"
GUEST_FULL_NAME = "Test Guest"
GUEST_ADDRESS = "123 Demo St, Miami, FL 33139"


def main():
    db = SessionLocal()
    try:
        # --- Owner ---
        owner = db.query(User).filter(User.email == OWNER_EMAIL, User.role == UserRole.owner).first()
        if owner:
            print(f"Owner already exists: {OWNER_EMAIL}")
        else:
            owner = User(
                email=OWNER_EMAIL,
                hashed_password=get_password_hash(OWNER_PASSWORD),
                role=UserRole.owner,
                full_name=OWNER_FULL_NAME,
                phone=None,
                state=None,
                city=None,
                country=None,
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(owner)
            db.flush()
            db.add(OwnerProfile(user_id=owner.id))
            print(f"Created owner: {OWNER_EMAIL}")

        # --- Guest ---
        guest = db.query(User).filter(User.email == GUEST_EMAIL, User.role == UserRole.guest).first()
        if guest:
            print(f"Guest already exists: {GUEST_EMAIL}")
        else:
            guest = User(
                email=GUEST_EMAIL,
                hashed_password=get_password_hash(GUEST_PASSWORD),
                role=UserRole.guest,
                full_name=GUEST_FULL_NAME,
                phone=None,
                state=None,
                city=None,
                country=None,
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None,
            )
            db.add(guest)
            db.flush()
            db.add(GuestProfile(
                user_id=guest.id,
                full_legal_name=GUEST_FULL_NAME,
                permanent_home_address=GUEST_ADDRESS,
                gps_checkin_acknowledgment=False,
            ))
            print(f"Created guest: {GUEST_EMAIL}")

        db.commit()

        print("\n--- Test users (use when verification email is not set up) ---")
        print("Owner:")
        print(f"  Email:    {OWNER_EMAIL}")
        print(f"  Password: {OWNER_PASSWORD}")
        print("  → Log in via Owner Login / Login page")
        print("\nGuest:")
        print(f"  Email:    {GUEST_EMAIL}")
        print(f"  Password: {GUEST_PASSWORD}")
        print("  → Log in via Guest Login page")
        print("\nDone.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
