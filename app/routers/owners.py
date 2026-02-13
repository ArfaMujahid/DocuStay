"""Module B1: Owner onboarding."""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.owner import OwnerProfile, Property, USAT_TOKEN_STAGED, USAT_TOKEN_RELEASED
from app.models.invitation import Invitation
from app.models.guest import PurposeOfStay, RelationshipToOwner
from app.schemas.owner import PropertyCreate, PropertyResponse, PropertyUpdate, ReleaseUsatTokenRequest
from app.dependencies import get_current_user, require_owner
from app.models.stay import Stay
from app.models.guest import GuestProfile
from app.services.audit_log import create_log, CATEGORY_STATUS_CHANGE, CATEGORY_SHIELD_MODE

router = APIRouter(prefix="/owners", tags=["owners"])

_PURPOSE_MAP = {"visit": PurposeOfStay.travel, "vacation": PurposeOfStay.travel, "caregiving": PurposeOfStay.personal, "house_sitting": PurposeOfStay.personal}
_REL_MAP = {"friend": RelationshipToOwner.friend, "family": RelationshipToOwner.family, "acquaintance": RelationshipToOwner.other, "tenant_applicant": RelationshipToOwner.other}


class InvitationCreate(BaseModel):
    owner_id: str | None = None
    property_id: int | None = None
    guest_name: str = ""
    guest_email: str = ""
    guest_phone: str = ""
    relationship: str = "friend"
    purpose: str = "visit"
    checkin_date: str = ""
    checkout_date: str = ""
    personal_message: str = ""
    # Dead Man's Switch: auto-protect when lease ends without owner response
    dead_mans_switch_enabled: bool = False
    dead_mans_switch_alert_email: bool = True
    dead_mans_switch_alert_sms: bool = False
    dead_mans_switch_alert_dashboard: bool = True
    dead_mans_switch_alert_phone: bool = False
    # When only guest_name + property_id are sent, checkin/checkout default to today + 14 days


def _ensure_property_usat_token(prop: Property, db: Session) -> None:
    """Backfill USAT token for properties created before staged tokens were added."""
    if prop.usat_token:
        return
    token = "USAT-" + secrets.token_hex(12).upper()
    for _ in range(10):
        if db.query(Property).filter(Property.usat_token == token).first() is None:
            break
        token = "USAT-" + secrets.token_hex(12).upper()
    else:
        token = f"USAT-{secrets.token_hex(8).upper()}-{prop.id}"
    prop.usat_token = token
    prop.usat_token_state = USAT_TOKEN_STAGED
    db.add(prop)


@router.get("/properties", response_model=list[PropertyResponse])
def list_my_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
    inactive: bool = False,
):
    """List properties. Default: active only (for dashboard main list and invite dropdown). inactive=1: inactive only (soft-deleted)."""
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        return []
    if inactive:
        props = db.query(Property).filter(
            Property.owner_profile_id == profile.id,
            Property.deleted_at.isnot(None),
        ).all()
    else:
        props = db.query(Property).filter(
            Property.owner_profile_id == profile.id,
            Property.deleted_at.is_(None),
        ).all()
    for p in props:
        if not p.usat_token:
            _ensure_property_usat_token(p, db)
    db.commit()
    return [PropertyResponse.model_validate(p) for p in props]


@router.post("/properties", response_model=PropertyResponse)
def add_property(
    data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    street = data.street_address or data.street
    if not street:
        raise HTTPException(status_code=400, detail="street or street_address required")
    region = (data.region_code or data.state or "US").upper()[:20]
    owner_occ = data.owner_occupied if data.owner_occupied is not None else data.is_primary_residence
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        profile = OwnerProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    def _generate_usat_token() -> str:
        return "USAT-" + secrets.token_hex(12).upper()

    prop = Property(
        owner_profile_id=profile.id,
        name=data.property_name,
        street=street,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        region_code=region,
        owner_occupied=owner_occ,
        property_type=data.property_type_enum,
        property_type_label=data.property_type,
        bedrooms=data.bedrooms,
    )
    db.add(prop)
    db.flush()
    for _ in range(10):
        token = _generate_usat_token()
        if db.query(Property).filter(Property.usat_token == token).first() is None:
            prop.usat_token = token
            prop.usat_token_state = USAT_TOKEN_STAGED
            break
    else:
        prop.usat_token = _generate_usat_token() + "-" + str(prop.id)
        prop.usat_token_state = USAT_TOKEN_STAGED
    db.commit()
    db.refresh(prop)
    return PropertyResponse.model_validate(prop)


@router.get("/properties/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No owner profile")
    prop = db.query(Property).filter(
        Property.id == property_id,
        Property.owner_profile_id == profile.id,
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyResponse.model_validate(prop)


@router.post("/properties/{property_id}/release-usat-token", response_model=PropertyResponse)
def release_usat_token(
    request: Request,
    property_id: int,
    data: ReleaseUsatTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Release the property's USAT token to the selected guest stay(s). Only those guests will see the token. Owner must choose at least one active stay for this property."""
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No owner profile")
    prop = _get_owner_property(property_id, profile, db)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.usat_token:
        raise HTTPException(status_code=400, detail="This property has no USAT token.")
    if not data.stay_ids:
        raise HTTPException(status_code=400, detail="Select at least one guest to release the token to.")
    now = datetime.now(timezone.utc)
    released_to_stays = []
    for stay_id in data.stay_ids:
        stay = db.query(Stay).filter(
            Stay.id == stay_id,
            Stay.property_id == property_id,
            Stay.owner_id == current_user.id,
            Stay.checked_out_at.is_(None),
            Stay.cancelled_at.is_(None),
        ).first()
        if not stay:
            raise HTTPException(
                status_code=400,
                detail=f"Stay {stay_id} is not an active stay for this property. Only current guests can receive the token.",
            )
        stay.usat_token_released_at = now
        db.add(stay)
        released_to_stays.append(stay)
    # Clear token from active stays at this property that were not selected (so Manage can revoke)
    other_active = (
        db.query(Stay)
        .filter(
            Stay.property_id == property_id,
            Stay.owner_id == current_user.id,
            Stay.checked_out_at.is_(None),
            Stay.cancelled_at.is_(None),
            Stay.id.notin_(data.stay_ids),
        )
        .all()
    )
    for stay in other_active:
        stay.usat_token_released_at = None
        db.add(stay)
    prop.usat_token_state = USAT_TOKEN_RELEASED
    prop.usat_token_released_at = now

    property_name = (prop.name or f"{prop.city}, {prop.state}" if prop else None) or "Property"
    guest_names = []
    for s in released_to_stays:
        guest = db.query(User).filter(User.id == s.guest_id).first()
        gp = db.query(GuestProfile).filter(GuestProfile.user_id == s.guest_id).first()
        name = (gp.full_legal_name if gp else None) or (guest.full_name if guest else None) or (guest.email if guest else "Unknown")
        guest_names.append(name)
    guest_list = ", ".join(guest_names)
    create_log(
        db,
        CATEGORY_STATUS_CHANGE,
        "USAT token released",
        f"USAT token released for property {property_name} to guest(s): {guest_list}. Stay IDs: {data.stay_ids}.",
        property_id=property_id,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        ip_address=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "").strip() or None,
        meta={"stay_ids": data.stay_ids, "guest_names": guest_names, "property_name": property_name},
    )
    db.commit()
    db.refresh(prop)
    return PropertyResponse.model_validate(prop)


def _get_owner_property(property_id: int, profile: OwnerProfile, db: Session) -> Property | None:
    return db.query(Property).filter(
        Property.id == property_id,
        Property.owner_profile_id == profile.id,
    ).first()


def _snapshot_property(prop: Property) -> dict:
    """Current property fields that can be updated (for change detection)."""
    return {
        "name": prop.name,
        "street": prop.street,
        "city": prop.city,
        "state": prop.state,
        "zip_code": prop.zip_code,
        "region_code": prop.region_code,
        "owner_occupied": prop.owner_occupied,
        "property_type": prop.property_type.value if prop.property_type else None,
        "property_type_label": prop.property_type_label,
        "bedrooms": prop.bedrooms,
        "shield_mode_enabled": getattr(prop, "shield_mode_enabled", 0),
    }


@router.put("/properties/{property_id}", response_model=PropertyResponse)
def update_property(
    request: Request,
    property_id: int,
    data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No owner profile")
    prop = _get_owner_property(property_id, profile, db)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    old = _snapshot_property(prop)

    if data.property_name is not None:
        prop.name = data.property_name
    if data.street_address is not None or data.street is not None:
        prop.street = (data.street_address or data.street or prop.street)
    if data.city is not None:
        prop.city = data.city
    if data.state is not None:
        prop.state = data.state
    if data.zip_code is not None:
        prop.zip_code = data.zip_code
    if data.region_code is not None:
        prop.region_code = data.region_code.upper()[:20]
    if data.owner_occupied is not None:
        prop.owner_occupied = data.owner_occupied
    if data.is_primary_residence is not None and data.owner_occupied is None:
        prop.owner_occupied = data.is_primary_residence
    if data.property_type_enum is not None:
        prop.property_type = data.property_type_enum
    if data.property_type is not None:
        prop.property_type_label = data.property_type
    if data.bedrooms is not None:
        prop.bedrooms = data.bedrooms
    # Owner can only turn Shield Mode OFF; it turns on automatically on the last day of a guest's stay
    if data.shield_mode_enabled is not None and data.shield_mode_enabled is False:
        prop.shield_mode_enabled = 0

    new = _snapshot_property(prop)
    changes = []
    changes_meta = {}
    for key in old:
        ov, nv = old[key], new[key]
        if nv is not None and getattr(nv, "value", None) is not None:
            nv = getattr(nv, "value", nv)
        if ov is not None and getattr(ov, "value", None) is not None:
            ov = getattr(ov, "value", ov)
        if ov != nv:
            changes.append(f"{key}: {ov!r} → {nv!r}")
            changes_meta[key] = {"old": ov, "new": nv}

    if changes:
        db.flush()
        ip = request.client.host if request.client else None
        ua = (request.headers.get("user-agent") or "").strip() or None
        property_name = (prop.name or "").strip() or f"{prop.city}, {prop.state}".strip(", ") or f"Property {property_id}"
        create_log(
            db,
            CATEGORY_STATUS_CHANGE,
            "Property updated",
            f"Owner updated property: {property_name} (id={property_id}). Changes: " + "; ".join(changes),
            property_id=prop.id,
            actor_user_id=current_user.id,
            actor_email=current_user.email,
            ip_address=ip,
            user_agent=ua,
            meta={"property_id": property_id, "property_name": property_name, "changes": changes_meta},
        )
        if "shield_mode_enabled" in changes_meta and changes_meta["shield_mode_enabled"].get("new") == 0:
            create_log(
                db,
                CATEGORY_SHIELD_MODE,
                "Shield Mode turned off",
                f"Owner turned off Shield Mode for {property_name}.",
                property_id=prop.id,
                actor_user_id=current_user.id,
                actor_email=current_user.email,
                ip_address=ip,
                user_agent=ua,
                meta={"property_id": property_id, "property_name": property_name},
            )
    db.commit()
    db.refresh(prop)
    return PropertyResponse.model_validate(prop)


def _has_active_stay(db: Session, property_id: int) -> bool:
    """True if there is any stay at this property that is not checked out and not cancelled."""
    return (
        db.query(Stay)
        .filter(
            Stay.property_id == property_id,
            Stay.checked_out_at.is_(None),
            Stay.cancelled_at.is_(None),
        )
        .first()
        is not None
    )


@router.delete("/properties/{property_id}")
def delete_property(
    request: Request,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Soft-delete property: set deleted_at so it is hidden from dashboard and invite list; can be reactivated. Only allowed when there is no active stay (past stays are OK). Data is kept for logs."""
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No owner profile")
    prop = _get_owner_property(property_id, profile, db)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.deleted_at is not None:
        return {"status": "success", "message": "Property is already inactive."}
    if _has_active_stay(db, property_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot remove property: it has an active guest stay. Wait for the stay to end or be cancelled first.",
        )
    property_name = (prop.name or "").strip() or f"{prop.city}, {prop.state}".strip(", ") or f"Property {property_id}"
    ip = request.client.host if request.client else None
    ua = (request.headers.get("user-agent") or "").strip() or None
    create_log(
        db,
        CATEGORY_STATUS_CHANGE,
        "Property deleted",
        f"Owner removed property from dashboard (inactive): {property_name} (id={property_id}, {prop.city}, {prop.state}). Data retained for logs.",
        property_id=property_id,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip,
        user_agent=ua,
        meta={"property_id": property_id, "property_name": property_name},
    )
    db.commit()
    prop.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "message": "Property removed from dashboard. It has been moved to Inactive properties and can be reactivated."}


@router.post("/properties/{property_id}/reactivate", response_model=PropertyResponse)
def reactivate_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Reactivate an inactive (soft-deleted) property so it appears in dashboard and invite list again."""
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No owner profile")
    prop = _get_owner_property(property_id, profile, db)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.deleted_at is None:
        db.refresh(prop)
        return PropertyResponse.model_validate(prop)
    prop.deleted_at = None
    db.commit()
    db.refresh(prop)
    return PropertyResponse.model_validate(prop)


@router.post("/invitations")
def create_invitation(
    request: Request,
    data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a guest invitation; store it and return code for the link."""
    prop_id = data.property_id
    if not prop_id:
        raise HTTPException(status_code=400, detail="property_id required")
    profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Owner profile not found")
    prop = db.query(Property).filter(Property.id == prop_id, Property.owner_profile_id == profile.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Cannot create invitation for an inactive property. Reactivate the property first.")
    if not (data.guest_name or "").strip():
        raise HTTPException(status_code=400, detail="guest_name is required")
    if not data.checkin_date or not data.checkout_date:
        raise HTTPException(status_code=400, detail="checkin_date and checkout_date are required")
    start = datetime.strptime(data.checkin_date, "%Y-%m-%d").date()
    end = datetime.strptime(data.checkout_date, "%Y-%m-%d").date()
    if end <= start:
        raise HTTPException(status_code=400, detail="checkout_date must be after checkin_date")
    code = "INV-" + secrets.token_hex(4).upper()
    purpose = _PURPOSE_MAP.get((data.purpose or "visit").lower(), PurposeOfStay.travel)
    rel = _REL_MAP.get((data.relationship or "friend").lower(), RelationshipToOwner.friend)
    # Dead Man's Switch is always on: triggered automatically; alerts by Email and Dashboard notification
    dms = 1
    dms_email = 1
    dms_sms = 0
    dms_dash = 1
    dms_phone = 0
    inv = Invitation(
        invitation_code=code,
        owner_id=current_user.id,
        property_id=prop.id,
        guest_name=(data.guest_name or "").strip() or None,
        guest_email=(data.guest_email or "").strip() or None,
        stay_start_date=start,
        stay_end_date=end,
        purpose_of_stay=purpose,
        relationship_to_owner=rel,
        region_code=prop.region_code,
        status="pending",
        dead_mans_switch_enabled=dms,
        dead_mans_switch_alert_email=dms_email,
        dead_mans_switch_alert_sms=dms_sms,
        dead_mans_switch_alert_dashboard=dms_dash,
        dead_mans_switch_alert_phone=dms_phone,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    ip = request.client.host if request.client else None
    ua = (request.headers.get("user-agent") or "").strip() or None
    create_log(
        db,
        CATEGORY_STATUS_CHANGE,
        "Invitation created",
        f"Owner created invitation {code} for property {prop.id}, guest {data.guest_name or data.guest_email or '—'}, {start}–{end}.",
        property_id=prop.id,
        invitation_id=inv.id,
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip,
        user_agent=ua,
        meta={"invitation_code": code, "guest_name": (data.guest_name or "").strip(), "guest_email": (data.guest_email or "").strip()},
    )
    db.commit()
    return {"invitation_code": code}


@router.get("/invitation-details")
def get_invitation_details(
    code: str,
    db: Session = Depends(get_db),
):
    """Public: get invitation details by code for the invite signup page (pending only)."""
    code = code.strip().upper()
    inv = db.query(Invitation).filter(Invitation.invitation_code == code, Invitation.status == "pending").first()
    if not inv:
        return {"valid": False}
    prop = db.query(Property).filter(Property.id == inv.property_id).first()
    owner = db.query(User).filter(User.id == inv.owner_id).first()
    return {
        "valid": True,
        "property_name": prop.name if prop else None,
        "property_address": f"{prop.street}, {prop.city}, {prop.state}{(' ' + prop.zip_code) if (prop and prop.zip_code) else ''}" if prop else None,
        "stay_start_date": str(inv.stay_start_date),
        "stay_end_date": str(inv.stay_end_date),
        "region_code": inv.region_code,
        "host_name": (owner.full_name if owner else None) or (owner.email if owner else ""),
        "guest_name": inv.guest_name,
    }
