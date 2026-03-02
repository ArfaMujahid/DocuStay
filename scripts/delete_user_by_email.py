"""
Delete a user by email and all dependent records.
Run from project root: python scripts/delete_user_by_email.py <email>
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/delete_user_by_email.py <email>")
        sys.exit(1)
    email = sys.argv[1].strip()

    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.models.owner import OwnerProfile, Property
    from app.models.guest import GuestProfile
    from app.models.invitation import Invitation
    from app.models.stay import Stay
    from app.models.guest_pending_invite import GuestPendingInvite
    from app.models.agreement_signature import AgreementSignature
    from app.models.audit_log import AuditLog
    from app.models.owner_poa_signature import OwnerPOASignature

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            return

        uid = user.id
        role = user.role.value if user.role else "?"

        # Delete in dependency order
        db.query(Stay).filter((Stay.owner_id == uid) | (Stay.guest_id == uid)).delete(synchronize_session=False)
        db.query(Invitation).filter(Invitation.owner_id == uid).delete(synchronize_session=False)
        db.query(GuestPendingInvite).filter(GuestPendingInvite.user_id == uid).delete(synchronize_session=False)
        db.query(AgreementSignature).filter(AgreementSignature.used_by_user_id == uid).update(
            {"used_by_user_id": None}, synchronize_session=False
        )
        db.query(AuditLog).filter(AuditLog.actor_user_id == uid).update(
            {"actor_user_id": None}, synchronize_session=False
        )
        db.query(OwnerPOASignature).filter(OwnerPOASignature.used_by_user_id == uid).delete(synchronize_session=False)

        if role == "owner":
            profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).first()
            if profile:
                db.query(Property).filter(Property.owner_profile_id == profile.id).delete(synchronize_session=False)
                db.delete(profile)
        elif role == "guest":
            gp = db.query(GuestProfile).filter(GuestProfile.user_id == uid).first()
            if gp:
                db.delete(gp)

        db.delete(user)
        db.commit()
        print(f"Deleted user: {email} (id={uid}, role={role})")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
