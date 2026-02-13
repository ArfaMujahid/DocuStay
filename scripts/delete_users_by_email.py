"""
Delete all users with the given email (both owner and guest roles) and their related data.
Usage: python scripts/delete_users_by_email.py <email>
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User
from app.models.owner import OwnerProfile, Property
from app.models.guest import GuestProfile
from app.models.invitation import Invitation
from app.models.stay import Stay
from app.models.agreement_signature import AgreementSignature
from app.models.guest_pending_invite import GuestPendingInvite


def main():
    email = (sys.argv[1] or "").strip().lower()
    if not email:
        print("Usage: python scripts/delete_users_by_email.py <email>")
        sys.exit(1)

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.email == email).all()
        if not users:
            print(f"No users found with email: {email}")
            db.close()
            sys.exit(0)

        for user in users:
            uid = user.id
            role = user.role.value

            # Null out agreement signature reference (keep signature records)
            db.query(AgreementSignature).filter(AgreementSignature.used_by_user_id == uid).update(
                {AgreementSignature.used_by_user_id: None}
            )

            # Stays where user is owner or guest
            db.query(Stay).filter((Stay.owner_id == uid) | (Stay.guest_id == uid)).delete(synchronize_session=False)

            # Invitations (owner only)
            db.query(Invitation).filter(Invitation.owner_id == uid).delete()

            if role == "owner":
                profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).first()
                if profile:
                    db.query(Property).filter(Property.owner_profile_id == profile.id).delete()
                db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).delete()

            db.query(GuestProfile).filter(GuestProfile.user_id == uid).delete()
            db.query(GuestPendingInvite).filter(GuestPendingInvite.user_id == uid).delete()
            db.delete(user)
            print(f"Deleted user: {email} (role={role}, id={uid})")

        db.commit()
        print(f"Done. Deleted {len(users)} user(s) with email: {email}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
