"""Module E: Mini Jurisdiction Logic Resolver (deterministic, spec-aligned)."""
from sqlalchemy.orm import Session
from app.models.region_rule import RegionRule, StayClassification, RiskLevel
from app.schemas.jle import JLEInput, JLEResult


def resolve_jurisdiction(db: Session, inp: JLEInput) -> JLEResult | None:
    """Resolve legal classification and limits from region rules."""
    rule = db.query(RegionRule).filter(RegionRule.region_code == inp.region_code.upper()).first()
    if not rule:
        return None

    max_days = rule.max_stay_days
    classification = rule.stay_classification_label
    risk = rule.risk_level
    statutes = [rule.statute_reference] if rule.statute_reference else []

    # CA: allow extended if owner occupied (lodger branch)
    if rule.allow_extended_if_owner_occupied and inp.owner_occupied:
        # Lodger path: allow longer (e.g. 30+); use a higher cap for demo
        max_days = 90  # example; could be stored in rule
        classification = StayClassification.lodger
        statutes.append("CA Civil Code § 1946.5 (Single Lodger)")

    within = inp.stay_duration_days <= max_days
    compliance = "within_limit" if within else "exceeds_limit"
    message = None
    if not within:
        message = f"Stay of {inp.stay_duration_days} days exceeds maximum allowed {max_days} days for this region."

    return JLEResult(
        legal_classification=classification,
        maximum_allowed_duration_days=max_days,
        compliance_status=compliance,
        applicable_statutes=statutes,
        risk_level=risk,
        message=message,
    )
