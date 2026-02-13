"""Module F: Legal restrictions & law display (Owner / Guest views)."""
from datetime import date, datetime
from pydantic import BaseModel
from app.models.region_rule import StayClassification, RiskLevel


class OwnerInvitationView(BaseModel):
    """Owner view: invitation for dashboard guests list (pending and accepted)."""
    id: int
    invitation_code: str
    property_id: int
    property_name: str
    guest_name: str | None = None
    guest_email: str | None
    stay_start_date: date
    stay_end_date: date
    region_code: str
    status: str  # pending, accepted, cancelled
    created_at: datetime | None
    is_expired: bool = False  # True when pending and created_at older than 12 hours


class GuestPendingInviteView(BaseModel):
    """Guest view: one pending invitation to sign on dashboard."""
    invitation_code: str
    property_name: str
    stay_start_date: date
    stay_end_date: date
    host_name: str | None
    region_code: str


class OwnerStayView(BaseModel):
    """Owner view: guest name, dates, region, classification, max stay, risk, applicable laws."""
    stay_id: int
    property_id: int
    guest_name: str
    property_name: str
    stay_start_date: date
    stay_end_date: date
    region_code: str
    legal_classification: StayClassification
    max_stay_allowed_days: int
    risk_indicator: RiskLevel
    applicable_laws: list[str]
    revoked_at: datetime | None = None
    checked_out_at: datetime | None = None
    cancelled_at: datetime | None = None
    usat_token_released_at: datetime | None = None  # when set, this guest can see the USAT token
    dead_mans_switch_enabled: bool = False  # DMS on for this stay (alerts + auto-vacate if no owner action)


class GuestStayView(BaseModel):
    """Guest view: property, approved dates, region classification, legal notice and laws. usat_token when released; vacate_by when revoked."""
    stay_id: int
    property_name: str
    approved_stay_start_date: date
    approved_stay_end_date: date
    region_code: str
    region_classification: str
    legal_notice: str = "This stay does not grant tenancy or homestead rights."
    statute_reference: str | None = None
    plain_english_explanation: str | None = None
    applicable_laws: list[str] = []
    usat_token: str | None = None
    revoked_at: datetime | None = None
    vacate_by: str | None = None  # ISO datetime: revoked_at + 12 hours
    checked_out_at: datetime | None = None  # when set, stay is view-only (no Checkout button)
    cancelled_at: datetime | None = None  # when set, stay is view-only (no Cancel stay button)


class OwnerAuditLogEntry(BaseModel):
    """Single append-only audit log entry for owner logs view."""
    id: int
    property_id: int | None
    stay_id: int | None
    invitation_id: int | None
    category: str
    title: str
    message: str
    actor_user_id: int | None
    actor_email: str | None
    ip_address: str | None
    created_at: datetime
    property_name: str | None = None  # resolved for display

    class Config:
        from_attributes = True