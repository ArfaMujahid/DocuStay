"""Agreement document generation for invitation flows. Uses JurisdictionInfo from DB SOT when available."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models.invitation import Invitation
from app.models.owner import Property
from app.models.user import User
from app.services.jurisdiction_sot import JurisdictionInfo, get_jurisdiction_for_property


def fill_guest_signature_in_content(
    content: str, guest_name: str, signed_date: str, ip_address: str | None = None
) -> str:
    """Replace the blank guest signature line with the signer's name, date, and optionally IP."""
    # Patterns for guest/signature lines with blank underscores
    patterns = [
        (r"Signed:\s*_{10,}\s+Date:\s*_{10,}", f"Signed: {guest_name}   Date: {signed_date}"),
        (r"Licensee:\s*_{10,}\s+Date:\s*_{10,}", f"Licensee: {guest_name}   Date: {signed_date}"),
        (r"Occupant:\s*_{10,}\s+Date:\s*_{10,}", f"Occupant: {guest_name}   Date: {signed_date}"),
        (r"Guest:\s*_{10,}\s+Date:\s*_{10,}", f"Guest: {guest_name}   Date: {signed_date}"),
    ]
    result = content
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, count=1)
    if ip_address is not None and "IP Address:" in result:
        result = re.sub(r"IP Address:\s*_{10,}", f"IP Address: {ip_address}", result, count=1)
    return result


@dataclass(frozen=True)
class AgreementDoc:
    document_id: str
    region_code: str
    title: str
    content: str
    document_hash: str
    property_address: str | None
    stay_start_date: str | None
    stay_end_date: str | None
    host_name: str | None


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _format_address(prop: Property | None) -> str | None:
    if not prop:
        return None
    parts = [prop.street, prop.city, prop.state]
    if prop.zip_code:
        parts.append(prop.zip_code)
    return ", ".join([p for p in parts if p])


def _normalize_region(region_code: str) -> str:
    rc = (region_code or "").strip().upper()
    if rc in {"NY", "NYC"}:
        return "NYC"
    if rc in {"FL", "CA", "TX", "WA"}:
        return rc
    return rc or "US"


def _guest_acknowledgment_content(
    *,
    property_address: str | None,
    guest_name: str,
    checkin: str,
    checkout: str,
    statute_citation: str,
) -> str:
    """Build GUEST ACKNOWLEDGMENT body (facts only; no trespass/may result in/legal conclusions). Statute from jurisdiction lookup (zip → state → statute)."""
    prop_display = (property_address or "[Address, Unit]").strip()
    return f"""GUEST ACKNOWLEDGMENT

Property: {prop_display}
Guest: {guest_name}
Authorization Period: {checkin} to {checkout}

By signing below, you acknowledge:

1. You are authorized to occupy this property only during the period stated above.
2. This authorization is personal to you. It does not include the right to sublet, assign, or transfer.
3. During this period, you may:
   - Receive mail at this address.
   - Perform maintenance with owner consent.
   - Pay utility bills on behalf of the owner (if applicable).
4. None of the activities listed above create a tenancy or lease. Under {statute_citation}, a written lease is required for tenancy.
5. The owner has granted DocuStay authority to document occupancy (Master POA on file).

Your authorization expires automatically on {checkout}. Renewal requires a new acknowledgment.

Signed: __________________________  Date: ________________
IP Address: ______________________
"""


def _build_agreement_from_jurisdiction(
    jinfo: JurisdictionInfo,
    *,
    owner_name: str,
    guest_name: str,
    today: str,
    checkin: str,
    checkout: str,
    property_address: str | None,
) -> tuple[str, str]:
    """Build GUEST ACKNOWLEDGMENT title and content from JurisdictionInfo (SOT). Returns (title, content). Statute from jurisdiction lookup."""
    title = "GUEST ACKNOWLEDGMENT"
    statute_citation = "applicable state and local law"
    if jinfo.statutes:
        statute_citation = jinfo.statutes[0].citation
    content = _guest_acknowledgment_content(
        property_address=property_address,
        guest_name=guest_name,
        checkin=checkin,
        checkout=checkout,
        statute_citation=statute_citation,
    )
    return (title, content)


def build_invitation_agreement(
    db: Session,
    invitation_code: str,
    guest_full_name: str | None = None,
) -> AgreementDoc | None:
    code = (invitation_code or "").strip().upper()
    if not code:
        return None

    inv = db.query(Invitation).filter(Invitation.invitation_code == code, Invitation.status.in_(["pending", "ongoing"])).first()
    if not inv:
        return None

    prop = db.query(Property).filter(Property.id == inv.property_id).first()
    owner = db.query(User).filter(User.id == inv.owner_id).first()

    region = _normalize_region(inv.region_code or (prop.region_code if prop else ""))
    host_name = (owner.full_name if owner else None) or (owner.email if owner else None)
    property_address = _format_address(prop)

    # Keep the canonical agreement text stable for hashing/verification. We record
    # the signer's identity separately in the signature record.
    guest_name = "[Guest Name]"
    owner_name = (host_name or "").strip() or "[Owner Name]"
    today = date.today().strftime("%B %d, %Y")
    checkin = str(inv.stay_start_date) if inv.stay_start_date else "[Check-in Date]"
    checkout = str(inv.stay_end_date) if inv.stay_end_date else "[Check-out Date]"

    # Prefer JurisdictionInfo from DB SOT so statute citations and removal text are dynamic.
    jinfo = get_jurisdiction_for_property(db, prop.zip_code if prop else None, region)
    if jinfo is not None:
        title, content = _build_agreement_from_jurisdiction(
            jinfo,
            owner_name=owner_name,
            guest_name=guest_name,
            today=today,
            checkin=checkin,
            checkout=checkout,
            property_address=property_address,
        )
        document_id = f"DSA-{code}-{jinfo.region_code}"
        doc_hash = _sha256_hex(content)
        return AgreementDoc(
            document_id=document_id,
            region_code=jinfo.region_code,
            title=title,
            content=content,
            document_hash=doc_hash,
            property_address=property_address,
            stay_start_date=str(inv.stay_start_date) if inv.stay_start_date else None,
            stay_end_date=str(inv.stay_end_date) if inv.stay_end_date else None,
            host_name=host_name,
        )

    # Fallback: GUEST ACKNOWLEDGMENT with statute from region if available.
    title = "GUEST ACKNOWLEDGMENT"
    statute_citation = "applicable state and local law"
    jinfo_fallback = get_jurisdiction_for_property(db, prop.zip_code if prop else None, region)
    if jinfo_fallback and jinfo_fallback.statutes:
        statute_citation = jinfo_fallback.statutes[0].citation
    content = _guest_acknowledgment_content(
        property_address=property_address,
        guest_name=guest_name,
        checkin=checkin,
        checkout=checkout,
        statute_citation=statute_citation,
    )

    document_id = f"DSA-{code}-{region}"
    doc_hash = _sha256_hex(content)

    return AgreementDoc(
        document_id=document_id,
        region_code=region,
        title=title,
        content=content,
        document_hash=doc_hash,
        property_address=property_address,
        stay_start_date=str(inv.stay_start_date) if inv.stay_start_date else None,
        stay_end_date=str(inv.stay_end_date) if inv.stay_end_date else None,
        host_name=host_name,
    )


# --- Master Power of Attorney (owner onboarding) ---

POA_DOCUMENT_ID = "DSA-Master-POA"
POA_TITLE = "Master Power of Attorney (POA)"

POA_CONTENT = """Master Power of Attorney (POA)

Overview
The Master POA is a one-time, account-level legal document signed during initial onboarding that establishes DocuStay as the property owner's legal representative for all property protection activities.

1. Who Signs What?
Property Owners ONLY sign the Master POA
Guests DO NOT sign the Master POA
Guests sign a completely different document called the "Guest Agreement" (covered separately)

2. When Is It Signed?
During initial account registration (onboarding)
Before any properties can be added to the system
This is a one-time signature - it covers ALL properties the owner adds, now and in the future

3. What Does It Actually Do?
The Master POA legally designates DocuStay as the owner's "Authorized Agent" to:
- Issue utility authorization tokens (USAT)
- Communicate with utility companies on owner's behalf
- Generate legal evidence packages
- Maintain forensic audit trails
- Act as the "official record keeper" for property status

4. Applicable Law (Jurisdiction)
Jurisdiction-specific statutes, removal procedures, and guest-agreement language for each property are determined by that property's location (zip code and state/region) from DocuStay's jurisdiction database (single source of truth). The applicable law for each property is displayed on that property's live link page and is used when generating guest agreements and authority packages.

SIGNATURE (ELECTRONIC)
Owner: ________________________   Date: __________
"""


def build_owner_poa_document() -> tuple[str, str, str, str]:
    """Return (document_id, title, content, document_hash) for the Master POA."""
    content = POA_CONTENT.strip()
    doc_hash = _sha256_hex(content)
    return (POA_DOCUMENT_ID, POA_TITLE, content, doc_hash)


def poa_content_with_signature(content: str, signer_name: str, signed_date: str) -> str:
    """Append signature line to POA content for generating a signed PDF."""
    return content.rstrip() + f"\n\nSigned by {signer_name} on {signed_date}"


def _escape_for_reportlab(s: str) -> str:
    """Escape text for ReportLab Paragraph (XML-like markup)."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def agreement_content_to_pdf(title: str, content: str) -> bytes:
    """Generate a PDF from agreement title and content using reportlab. Content wraps to page width and is justified."""
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["Normal"].clone("JustifiedBody", alignment=TA_JUSTIFY, spaceAfter=6)

    story = [Paragraph(_escape_for_reportlab(title.replace("\n", " ")), title_style), Spacer(1, 0.2 * inch)]

    for line in content.splitlines():
        line = line.strip()
        if line:
            story.append(Paragraph(_escape_for_reportlab(line), body_style))
        else:
            story.append(Spacer(1, 0.12 * inch))

    doc.build(story)
    return buf.getvalue()
