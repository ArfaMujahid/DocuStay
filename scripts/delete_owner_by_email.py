"""Delete an owner user by email. Removes or unlinks all related data (stays, invitations, properties, POA link, audit refs, pending) then deletes the user."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.owner import OwnerProfile, Property
from app.models.invitation import Invitation
from app.models.stay import Stay
from app.models.owner_poa_signature import OwnerPOASignature
from app.models.audit_log import AuditLog
from app.models.pending_registration import PendingRegistration

EMAIL = "arfamujahid12@gmail.com"


def run():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == EMAIL.strip().lower(), User.role == UserRole.owner).first()
        if not user:
            print(f"No owner found with email: {EMAIL}")
            return

        uid = user.id
        print(f"Found owner id={uid}, email={user.email}. Deleting related data then user...")

        # Stays where this user is the owner
        stays = db.query(Stay).filter(Stay.owner_id == uid).all()
        for s in stays:
            db.delete(s)
        if stays:
            print(f"  Deleted {len(stays)} stay(s)")

        # Invitations created by this owner
        invs = db.query(Invitation).filter(Invitation.owner_id == uid).all()
        for inv in invs:
            db.delete(inv)
        if invs:
            print(f"  Deleted {len(invs)} invitation(s)")

        # Unlink POA signature (keep record, just unlink from user)
        db.query(OwnerPOASignature).filter(OwnerPOASignature.used_by_user_id == uid).update(
            {"used_by_user_id": None, "used_at": None}
        )
        print("  Unlinked Master POA signature(s)")

        # Audit log: keep entries but clear actor_user_id so we can delete user
        db.query(AuditLog).filter(AuditLog.actor_user_id == uid).update({"actor_user_id": None})
        print("  Cleared audit log actor_user_id references")

        # Properties via OwnerProfile
        profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == uid).first()
        if profile:
            props = db.query(Property).filter(Property.owner_profile_id == profile.id).all()
            for p in props:
                db.delete(p)
            if props:
                print(f"  Deleted {len(props)} property(ies)")
            db.delete(profile)
            print("  Deleted owner profile")

        # Pending registrations with this email (owner)
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.email == EMAIL.strip().lower(),
            PendingRegistration.role == UserRole.owner,
        ).all()
        for p in pending:
            db.delete(p)
        if pending:
            print(f"  Deleted {len(pending)} pending registration(s)")

        db.delete(user)
        db.commit()
        print(f"Deleted owner user: {EMAIL}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
