"""Billing service: onboarding fee (one-time) and monthly subscription.

Uses Stripe. Requirement 1: one-time onboarding fee at first property upload.
Requirement 2: monthly subscription = $1/unit baseline + $10/unit when Shield on.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.owner import OwnerProfile, Property
from app.models.user import User
from app.services.audit_log import create_log, CATEGORY_BILLING

logger = logging.getLogger(__name__)

# (min_units, max_units, amount_cents or per_unit_cents, flat=True means fixed amount)
_ONBOARDING_TIERS = [
    (1, 5, 29900, True),       # $299 flat
    (6, 20, 4900, False),      # $49/unit
    (21, 100, 2900, False),    # $29/unit
    (101, 500, 1900, False),   # $19/unit
    (501, 2000, 1400, False),  # $14/unit
    (2001, 10000, 1000, False), # $10/unit
    (10001, 999_999_999, 700, False),  # $7/unit
]


class OnboardingFeeResult(NamedTuple):
    """Result of onboarding fee calculation."""
    amount_cents: int
    description: str
    tier_label: str


def get_onboarding_fee(total_units: int) -> OnboardingFeeResult | None:
    """Compute onboarding fee for a given unit count. Returns None if total_units < 1."""
    if total_units < 1:
        return None
    for min_u, max_u, amount, flat in _ONBOARDING_TIERS:
        if min_u <= total_units <= max_u:
            if flat:
                amount_cents = amount
                tier_label = f"1-5 units ($299 flat)"
            else:
                amount_cents = amount * total_units
                tier_label = f"{min_u}-{max_u} units (${amount // 100}/unit)"
            desc = f"DocuStay onboarding fee ({total_units} unit{'s' if total_units != 1 else ''})"
            return OnboardingFeeResult(amount_cents=amount_cents, description=desc, tier_label=tier_label)
    return None


def _stripe_enabled() -> bool:
    s = get_settings()
    return bool((s.stripe_secret_key or "").strip())


def get_or_create_stripe_customer(profile: OwnerProfile, user: User) -> str | None:
    """Ensure Stripe customer exists for this owner; return stripe_customer_id or None if Stripe disabled."""
    if not _stripe_enabled():
        return None
    import stripe
    stripe.api_key = get_settings().stripe_secret_key
    if profile.stripe_customer_id:
        try:
            stripe.Customer.retrieve(profile.stripe_customer_id)
            return profile.stripe_customer_id
        except stripe.InvalidRequestError:
            pass
    email = (user.email or "").strip()
    name = (user.full_name or email or "DocuStay Owner").strip() or None
    customer = stripe.Customer.create(email=email or None, name=name, metadata={"owner_profile_id": str(profile.id)})
    return customer.id


def _count_units_and_shield(db: Session, profile: OwnerProfile) -> tuple[int, int]:
    """Return (unit_count, shield_count) for non-deleted properties. 1 unit = 1 property."""
    q = db.query(Property).filter(
        Property.owner_profile_id == profile.id,
        Property.deleted_at.is_(None),
    )
    total = q.count()
    shield = q.filter(Property.shield_mode_enabled == 1).count()
    return total, shield


def ensure_subscription(db: Session, profile: OwnerProfile) -> None:
    """Create Stripe subscription (baseline $1/unit + Shield $10/unit) if not already created. Idempotent."""
    if not _stripe_enabled() or not profile.stripe_customer_id:
        return
    if profile.stripe_subscription_id:
        try:
            import stripe
            stripe.api_key = get_settings().stripe_secret_key
            stripe.Subscription.retrieve(profile.stripe_subscription_id)
            return  # already exists and valid
        except Exception:
            pass  # subscription may have been cancelled; create new

    units, shield_units = _count_units_and_shield(db, profile)
    if units < 1:
        return

    import stripe
    stripe.api_key = get_settings().stripe_secret_key
    try:
        sub = stripe.Subscription.create(
            customer=profile.stripe_customer_id,
            items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": 100,  # $1 per unit
                        "recurring": {"interval": "month"},
                        "product_data": {"name": "DocuStay Baseline (per unit)"},
                    },
                    "quantity": units,
                },
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": 1000,  # $10 per unit
                        "recurring": {"interval": "month"},
                        "product_data": {"name": "DocuStay Shield (per unit)"},
                    },
                    "quantity": shield_units,
                },
            ],
            metadata={"owner_profile_id": str(profile.id)},
        )
        baseline_item_id: str | None = None
        shield_item_id: str | None = None
        items_data = getattr(sub, "items", None)
        if items_data is not None:
            data = getattr(items_data, "data", None) or []
            for item in data:
                price = getattr(item, "price", None)
                amt = getattr(price, "unit_amount", 0) or 0 if price else 0
                item_id = getattr(item, "id", None)
                if amt == 100 and item_id:
                    baseline_item_id = item_id
                elif amt == 1000 and item_id:
                    shield_item_id = item_id
        profile.stripe_subscription_id = sub.id
        profile.stripe_subscription_baseline_item_id = baseline_item_id
        profile.stripe_subscription_shield_item_id = shield_item_id
        db.commit()
        logger.info("Subscription created for profile_id=%s, units=%s, shield=%s", profile.id, units, shield_units)
    except stripe.StripeError as e:
        logger.exception("Stripe error creating subscription for profile_id=%s: %s", profile.id, e)
        raise


def sync_subscription_quantities(db: Session, profile: OwnerProfile) -> None:
    """Update Stripe subscription item quantities to match current DB (unit count and Shield count). Prorates automatically.
    When unit count goes to 0, cancels the subscription so we do not send quantity=0 (Stripe prorates and stops billing)."""
    if not _stripe_enabled() or not profile.stripe_subscription_id:
        return
    units, shield_units = _count_units_and_shield(db, profile)

    import stripe
    stripe.api_key = get_settings().stripe_secret_key
    try:
        if units <= 0:
            # Stop billing immediately: cancel subscription (prorated). Reactivating a property will create a new subscription.
            stripe.Subscription.cancel(profile.stripe_subscription_id, prorate=True)
            profile.stripe_subscription_id = None
            profile.stripe_subscription_baseline_item_id = None
            profile.stripe_subscription_shield_item_id = None
            db.commit()
            logger.info("Subscription cancelled for profile_id=%s (0 units); billing stopped (prorated).", profile.id)
            return
        items = []
        if profile.stripe_subscription_baseline_item_id:
            items.append({"id": profile.stripe_subscription_baseline_item_id, "quantity": units})
        if profile.stripe_subscription_shield_item_id:
            items.append({"id": profile.stripe_subscription_shield_item_id, "quantity": shield_units})
        if not items:
            return
        stripe.Subscription.modify(profile.stripe_subscription_id, items=items)
        logger.info("Subscription quantities synced for profile_id=%s: units=%s, shield=%s", profile.id, units, shield_units)
    except stripe.StripeError as e:
        logger.warning("Stripe error syncing subscription quantities for profile_id=%s: %s", profile.id, e)


def charge_onboarding_fee(
    db: Session,
    profile: OwnerProfile,
    user: User,
    total_units: int,
) -> str | None:
    """Create and finalize one-time onboarding invoice for this owner. Idempotent: no-op if already completed.

    Returns the Stripe hosted invoice URL so the user can pay, or None if Stripe disabled or already charged.
    """
    if total_units < 1:
        return None
    if profile.onboarding_billing_completed_at is not None:
        logger.info("Billing onboarding already completed for profile_id=%s, skipping", profile.id)
        return None

    fee = get_onboarding_fee(total_units)
    if not fee:
        return None

    if not _stripe_enabled():
        logger.warning("Stripe not configured; skipping onboarding charge for profile_id=%s", profile.id)
        # Still mark as "completed" so we don't retry when Stripe is added later (optional: don't set if you want to charge later)
        profile.onboarding_billing_completed_at = datetime.now(timezone.utc)
        profile.onboarding_billing_unit_count = total_units
        db.commit()
        return None

    import stripe
    stripe.api_key = get_settings().stripe_secret_key

    customer_id = get_or_create_stripe_customer(profile, user)
    if not customer_id:
        return None
    profile.stripe_customer_id = customer_id

    try:
        invoice = stripe.Invoice.create(
            customer=customer_id,
            collection_method="charge_automatically",  # charge immediately if customer has payment method; else invoice stays open and they can pay via hosted URL
            metadata={"owner_profile_id": str(profile.id), "onboarding_units": str(total_units)},
            description=fee.description,
        )
        stripe.InvoiceItem.create(
            customer=customer_id,
            invoice=invoice.id,
            amount=fee.amount_cents,
            currency="usd",
            description=fee.description,
        )
        stripe.Invoice.finalize_invoice(invoice.id)
        inv = stripe.Invoice.retrieve(invoice.id)
        hosted_url = inv.hosted_invoice_url
    except stripe.StripeError as e:
        logger.exception("Stripe error creating onboarding invoice for profile_id=%s: %s", profile.id, e)
        raise

    profile.onboarding_billing_completed_at = datetime.now(timezone.utc)
    profile.onboarding_billing_unit_count = total_units
    create_log(
        db,
        CATEGORY_BILLING,
        "Onboarding invoice created",
        f"Invoice for {total_units} unit(s), ${fee.amount_cents / 100:.2f} USD. Pay at the link in your email or from Billing.",
        property_id=None,
        actor_user_id=user.id,
        actor_email=user.email,
        meta={"stripe_invoice_id": inv.id, "amount_cents": fee.amount_cents, "unit_count": total_units},
    )
    db.commit()
    logger.info("Onboarding invoice created for profile_id=%s, units=%s, amount_cents=%s", profile.id, total_units, fee.amount_cents)
    # Requirement 2: create monthly subscription (baseline + Shield) after onboarding
    try:
        ensure_subscription(db, profile)
    except Exception as e:
        logger.warning("Subscription creation failed after onboarding (invoice already created): %s", e)
    return hosted_url


def on_onboarding_properties_completed(
    db: Session,
    profile: OwnerProfile,
    user: User,
    total_units: int,
) -> str | None:
    """Called when owner has just completed their first property upload. Charges onboarding fee (once). Returns hosted invoice URL or None."""
    return charge_onboarding_fee(db, profile, user, total_units)
