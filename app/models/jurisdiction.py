"""Jurisdiction SOT: single source of truth for jurisdiction rules, statutes, and zip-based lookup."""
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey, Text
from app.database import Base
from app.models.region_rule import StayClassification, RiskLevel


class Jurisdiction(Base):
    """One row per region (NYC, FL, CA, TX, WA). Drives authority wrap, agreements, JLE."""
    __tablename__ = "jurisdictions"

    id = Column(Integer, primary_key=True, index=True)
    region_code = Column(String(20), nullable=False, unique=True, index=True)  # NYC, FL, CA, TX, WA
    state_code = Column(String(10), nullable=False)  # NY, FL, CA, TX, WA
    name = Column(String(100), nullable=False)  # New York, Florida, California, ...

    max_stay_days = Column(Integer, nullable=False)
    tenancy_threshold_days = Column(Integer, nullable=True)
    warning_days = Column(Integer, nullable=True)

    agreement_type = Column(String(64), nullable=True)  # REVOCABLE_LICENSE, HB621_DECLARATION, ...
    removal_guest_text = Column(Text, nullable=True)
    removal_tenant_text = Column(Text, nullable=True)

    stay_classification_label = Column(SQLEnum(StayClassification), nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    allow_extended_if_owner_occupied = Column(Boolean, default=False)


class JurisdictionStatute(Base):
    """Statute citations and plain-English per jurisdiction. Multiple per region."""
    __tablename__ = "jurisdiction_statutes"

    id = Column(Integer, primary_key=True, index=True)
    region_code = Column(String(20), nullable=False, index=True)
    citation = Column(String(255), nullable=False)
    plain_english = Column(Text, nullable=True)
    use_in_authority_package = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)


class JurisdictionZipMapping(Base):
    """Zip code (5-digit) or zip prefix -> region_code. Deterministic lookup."""
    __tablename__ = "jurisdiction_zip_mappings"

    id = Column(Integer, primary_key=True, index=True)
    zip_code = Column(String(5), nullable=False, index=True)  # 5-digit zip
    region_code = Column(String(20), nullable=False, index=True)
