"""Module E: Mini Jurisdiction Logic Resolver (deterministic, spec-aligned). Uses jurisdiction SOT when available."""
from sqlalchemy.orm import Session
from app.models.region_rule import RegionRule, StayClassification, RiskLevel
from app.schemas.jle import JLEInput, JLEResult


def resolve_jurisdiction(db: Session, inp: JLEInput) -> JLEResult | None:
    """Resolve legal classification and limits. Prefer jurisdiction SOT (DB); fall back to region_rules."""
    from app.services.jurisdiction_sot import get_jurisdiction_for_region

    rc = inp.region_code.upper() if inp.region_code else ""
    jinfo = get_jurisdiction_for_region(db, rc)
    if jinfo:
        max_days = jinfo.max_stay_days
        classification = jinfo.stay_classification
        if jinfo.allow_extended_if_owner_occupied and inp.owner_occupied:
            max_days = 90
            classification = StayClassification.lodger
        statutes = [s.citation for s in jinfo.statutes]
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
            risk_level=jinfo.risk_level,
            message=message,
        )

    # Fallback: legacy region_rules
    rule = db.query(RegionRule).filter(RegionRule.region_code == rc).first()
    if not rule:
        return None

    max_days = rule.max_stay_days
    classification = rule.stay_classification_label
    risk = rule.risk_level
    statutes = [rule.statute_reference] if rule.statute_reference else []

    if rule.allow_extended_if_owner_occupied and inp.owner_occupied:
        max_days = 90
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
