"""Mark pending invitations that were not accepted within 12 hours as expired (status + token_state)."""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.invitation import Invitation

logger = logging.getLogger("uvicorn.error")
PENDING_INVITATION_EXPIRE_HOURS = 12


def run_invitation_cleanup_job() -> None:
    """Mark pending invitations older than 12 hours as expired: status='expired', token_state='EXPIRED'."""
    db: Session = SessionLocal()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(hours=PENDING_INVITATION_EXPIRE_HOURS)
        invs = db.query(Invitation).filter(
            Invitation.status == "pending",
            Invitation.created_at < threshold,
        ).all()
        for inv in invs:
            inv.status = "expired"
            inv.token_state = "EXPIRED"
            db.add(inv)
        db.commit()
        if invs:
            logger.info("Invitation cleanup: marked %d pending invitation(s) as expired (status=expired, token_state=EXPIRED).", len(invs))
    finally:
        db.close()
