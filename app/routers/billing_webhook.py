"""Stripe webhook for billing events. Logs invoice.paid to audit log."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.owner import OwnerProfile
from app.models.user import User
from app.services.audit_log import create_log, CATEGORY_BILLING

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events. Verifies signature and logs invoice.paid to audit."""
    settings = get_settings()
    secret = (settings.stripe_webhook_secret or "").strip()
    if not secret:
        raise HTTPException(status_code=501, detail="Stripe webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature")

    import stripe
    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}") from e
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}") from e

    if event.type == "invoice.paid":
        inv = event.data.object
        meta = getattr(inv, "metadata", None) or {}
        profile_id_str = meta.get("owner_profile_id")
        if not profile_id_str:
            logger.warning("invoice.paid missing owner_profile_id in metadata: %s", inv.id)
            return {"received": True}
        try:
            profile_id = int(profile_id_str)
        except (TypeError, ValueError):
            logger.warning("invoice.paid invalid owner_profile_id: %s", profile_id_str)
            return {"received": True}

        profile = db.query(OwnerProfile).filter(OwnerProfile.id == profile_id).first()
        if not profile:
            logger.warning("invoice.paid profile_id=%s not found", profile_id)
            return {"received": True}
        user = db.query(User).filter(User.id == profile.user_id).first()
        amount_paid = getattr(inv, "amount_paid", 0) or 0
        currency = (getattr(inv, "currency", None) or "usd").upper()
        create_log(
            db,
            CATEGORY_BILLING,
            "Invoice paid",
            f"Invoice {getattr(inv, 'number', inv.id)} paid: ${amount_paid / 100:.2f} {currency}.",
            property_id=None,
            actor_user_id=user.id if user else None,
            actor_email=user.email if user else None,
            meta={"stripe_invoice_id": inv.id, "amount_paid_cents": amount_paid, "currency": currency},
        )
        # If this is the onboarding invoice (metadata has onboarding_units), mark profile so owner can invite guests
        if meta.get("onboarding_units") and profile.onboarding_invoice_paid_at is None:
            from datetime import datetime, timezone
            profile.onboarding_invoice_paid_at = datetime.now(timezone.utc)
            logger.info("Set onboarding_invoice_paid_at for profile_id=%s (invoice %s)", profile_id, inv.id)
        db.commit()
        logger.info("Logged invoice.paid for profile_id=%s invoice=%s", profile_id, inv.id)

    return {"received": True}
