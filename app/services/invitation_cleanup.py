"""Delete pending invitations that were not accepted within 12 hours."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.invitation import Invitation

PENDING_INVITATION_EXPIRE_HOURS = 12


def run_invitation_cleanup_job() -> None:
    """Delete all pending invitations older than 12 hours."""
    db: Session = SessionLocal()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(hours=PENDING_INVITATION_EXPIRE_HOURS)
        deleted = db.query(Invitation).filter(
            Invitation.status == "pending",
            Invitation.created_at < threshold,
        ).delete()
        db.commit()
        if deleted:
            import logging
            logging.getLogger("uvicorn.error").info("Invitation cleanup: deleted %d expired pending invitation(s).", deleted)
    finally:
        db.close()
