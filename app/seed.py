"""Module D: Seed region rules (NYC, FL, CA, TX) from spec."""
from sqlalchemy.orm import Session
from app.models.region_rule import RegionRule, StayClassification, RiskLevel


def seed_region_rules(db: Session) -> None:
    if db.query(RegionRule).count() > 0:
        return
    rules = [
        RegionRule(
            region_code="NYC",
            max_stay_days=29,
            stay_classification_label=StayClassification.guest,
            risk_level=RiskLevel.high,
            statute_reference="NYC Admin Code § 26-521",
            plain_english_explanation="Occupying a dwelling for 30 consecutive days creates tenancy rights. Max 29 days.",
            allow_extended_if_owner_occupied=False,
        ),
        RegionRule(
            region_code="FL",
            max_stay_days=30,
            stay_classification_label=StayClassification.guest,
            risk_level=RiskLevel.medium,
            statute_reference="FL Statute § 82.036 (HB 621)",
            plain_english_explanation="Sheriff may remove unauthorized person with signed affidavit; no lease.",
            allow_extended_if_owner_occupied=False,
        ),
        RegionRule(
            region_code="CA",
            max_stay_days=29,
            stay_classification_label=StayClassification.guest,
            risk_level=RiskLevel.medium,
            statute_reference="CA Civil Code § 1940.1, AB 1482",
            plain_english_explanation="Transient occupancy; 30+ days creates tenancy. Lodger if owner lives in.",
            allow_extended_if_owner_occupied=True,
        ),
        RegionRule(
            region_code="TX",
            max_stay_days=29,
            stay_classification_label=StayClassification.guest,
            risk_level=RiskLevel.medium,
            statute_reference="Texas Property Code § 92.001, Penal Code § 30.05",
            plain_english_explanation="Transient housing exempt from landlord-tenant; criminal trespass after notice.",
            allow_extended_if_owner_occupied=False,
        ),
        RegionRule(
            region_code="WA",
            max_stay_days=29,
            stay_classification_label=StayClassification.guest,
            risk_level=RiskLevel.medium,
            statute_reference="RCW 9A.52.105",
            plain_english_explanation="Tenancy is fact-specific; owner declaration can assist police removal in defined cases.",
            allow_extended_if_owner_occupied=False,
        ),
    ]
    for r in rules:
        db.add(r)
    db.commit()
