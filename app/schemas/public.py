"""Schemas for public live property page and portfolio (no auth)."""
from datetime import date, datetime

from pydantic import BaseModel


# --- Portfolio (owner public page) ---


class PortfolioPropertyItem(BaseModel):
    """Single property for portfolio listing (public info only)."""
    id: int
    name: str | None
    city: str
    state: str
    region_code: str
    property_type_label: str | None = None
    bedrooms: str | None = None


class PortfolioOwnerInfo(BaseModel):
    """Owner basic info for portfolio page."""
    full_name: str | None = None
    email: str = ""
    phone: str | None = None
    state: str | None = None


class PortfolioPagePayload(BaseModel):
    """Payload for GET /public/portfolio/{slug}."""
    owner: PortfolioOwnerInfo
    properties: list[PortfolioPropertyItem] = []


class LivePropertyInfo(BaseModel):
    """Property summary for live page."""
    name: str | None
    street: str
    city: str
    state: str
    zip_code: str | None
    region_code: str
    occupancy_status: str  # vacant | occupied | unknown | unconfirmed
    shield_mode_enabled: bool  # mode: when True = PASSIVE GUARD or ACTIVE MONITORING
    token_state: str = "staged"  # staged | released – for Quick Decision layer


class LiveOwnerInfo(BaseModel):
    """Owner contact for live page."""
    full_name: str | None
    email: str
    phone: str | None


class LiveCurrentGuestInfo(BaseModel):
    """Current guest and stay for live page."""
    guest_name: str
    stay_start_date: date
    stay_end_date: date
    checked_out_at: datetime | None  # when set, guest has checked out
    dead_mans_switch_enabled: bool


class LiveStaySummary(BaseModel):
    """Past or upcoming stay summary."""
    guest_name: str
    stay_start_date: date
    stay_end_date: date
    checked_out_at: datetime | None = None


class LiveLogEntry(BaseModel):
    """Single audit log entry for property (public view)."""
    category: str
    title: str
    message: str
    created_at: datetime


class LivePropertyPagePayload(BaseModel):
    """Full payload for GET /api/public/live/{slug} – evidence view."""
    has_current_guest: bool
    property: LivePropertyInfo
    owner: LiveOwnerInfo
    current_guest: LiveCurrentGuestInfo | None = None
    last_stay: LiveStaySummary | None = None
    upcoming_stays: list[LiveStaySummary] = []
    logs: list[LiveLogEntry] = []
    # Quick Decision / evidence layer
    authorization_state: str  # ACTIVE | NONE | EXPIRED | REVOKED
    record_id: str  # live_slug for re-verification
    generated_at: datetime
    # Authority layer (Master POA)
    poa_signed_at: datetime | None = None
    poa_signature_id: int | None = None  # for View POA link
