"""
Delete a property owner account by email (and all related data).
Usage: python scripts/delete_owner_by_email.py <email>
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.owner import OwnerProfile, Property
from app.models.invitation import Invitation
from app.models.stay import Stay


def main():
    email = (sys.argv[1] or "").strip().lower()
    if not email:
        print("Usage: python scripts/delete_owner_by_email.py <email>")
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.role == UserRole.owner).first()
        if not user:
            print(f"No property owner found with email: {email}")
            sys.exit(1)

        uid = user.id
        profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).first()
        profile_id = profile.id if profile else None

        db.query(Stay).filter(Stay.owner_id == uid).delete()
        db.query(Invitation).filter(Invitation.owner_id == uid).delete()
        if profile_id is not None:
            db.query(Property).filter(Property.owner_profile_id == profile_id).delete()
        db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).delete()
        db.delete(user)
        db.commit()
        print(f"Deleted property owner: {email}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
