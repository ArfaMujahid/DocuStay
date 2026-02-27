"""
Generate Docustay Requirements Status PDF.
Run from project root: python scripts/generate_requirements_pdf.py
Output: docs/Docustay_Requirements_Status.pdf
"""
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_styles(styles):
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=24,
            textColor=colors.HexColor("#1a365d"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2c5282"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#2d3748"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocBullet",
            parent=styles["Normal"],
            fontSize=10,
            leftIndent=18,
            spaceAfter=4,
            bulletIndent=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocBody",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocNote",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#718096"),
            spaceAfter=4,
            leftIndent=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="UnclearHeading",
            parent=styles["Heading1"],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#744210"),
        )
    )
    return styles


# --- CONTENT: COMPLETED (DONE) ---
DONE_ITEMS = [
    (
        "Identity Verification (Owner/Manager)",
        [
            "Third-party KYC required for Owner of Record and Authorized Agent before any property or Master POA.",
            "Verification includes: Government-issued ID upload, OCR data extraction, selfie + liveness verification, identity match validation.",
            "Trigger: After account creation, before signing Master POA, before adding any property, before accessing operational dashboard.",
            "Preferred vendors: Stripe Identity, Persona, or equivalent biometric-linked KYC providers.",
        ],
    ),
    (
        "Status State Machine",
        [
            "Every unit supports four states: VACANT, OCCUPIED, UNKNOWN, UNCONFIRMED.",
            "UNCONFIRMED used when the system prompted for confirmation (e.g. after Dead Man's Switch) and received no response.",
            "UNKNOWN for never set or unknown; UNCONFIRMED for we asked, no answer.",
            "System must not stay on the old label when confirmation is ignored; it flips to UNCONFIRMED. Recorded silence is evidence.",
        ],
    ),
    (
        "Dead-Man Switch Rules",
        [
            "48 hours before lease end: first confirmation prompt.",
            "Lease end date: no automatic status change.",
            "48 hours after lease end with no owner action: status flips to UNCONFIRMED (not at midnight on lease end).",
            "Explicit confirmation action in UI: Unit Vacated, Lease Renewed (with new lease end date), or Holdover. If no selection before deadline, transition to UNCONFIRMED and log.",
            "Return from UNCONFIRMED only after authenticated user explicitly confirms; previous status, new status, identity, and timestamp recorded.",
        ],
    ),
    (
        "Append-Only Protocol & No Deletion",
        [
            "Properties are archived, never hard-deleted. Audit log is append-only.",
            "Every status change timestamped (UTC); every guest signature logged; every failed attempt recorded.",
            "Mistakes remain part of the permanent record. DocuStay acts as Independent Third-Party Recorder under Rule 803(6).",
        ],
    ),
    (
        "Master POA System",
        [
            "One Master POA per owner entity at account level, signed before any properties are added.",
            "Designates DocuStay as Authorized Agent of Record; creates legal Chain of Command and self-authenticating business records under FRE 803(6).",
        ],
    ),
    (
        "Zip-Code Utility Bucket Mapping",
        [
            "At property registration (including bulk CSV), system uses ZIP to identify local utility providers (electric, water, gas, internet).",
            "Automatically generates Authority Letters to those utilities notifying them DocuStay is the only authorized agent for burn-in codes at those addresses.",
        ],
    ),
    (
        "Pre-Generated Token Placeholder (Staged Tokens)",
        [
            "Every property receives a unique token immediately upon registration, before any guest.",
            "Token exists from Day 1 in Staged state until owner releases it to a verified tenant or it is burned.",
        ],
    ),
    (
        "Multi-Switch Dashboard Architecture",
        [
            "Two independent toggles per unit: (1) Occupancy Status: VACANT / OCCUPIED; (2) Shield Mode: ON / OFF.",
            "Shield Mode is documentation posture ($10/month when ON); can be ON or OFF regardless of occupancy.",
            "Gap Filter: tool for portfolios to find units that are VACANT but have Shield Mode OFF (vulnerable properties).",
        ],
    ),
    (
        "Dead Man's Switch Implementation",
        [
            "Trigger prompts near lease or authorization end points; log confirmations when they occur.",
            "If ignored, transition unit to UNCONFIRMED; continue prompting on a defined schedule.",
            "System never infers vacancy or occupancy due to silence.",
        ],
    ),
    (
        "Bulk Operations & Portfolio Management",
        [
            "CSV bulk upload for properties to support enterprise-level property managers with hundreds or thousands of units.",
        ],
    ),
    (
        "Dynamic Agreement Generation",
        [
            "Base template (e.g. Revocable License); clause injection by jurisdiction and risk (e.g. Nature of Relationship, Non-Exclusive Possession, Utility Prohibition); variable filling (dates, expiry); PDF locked and sent for e-signature.",
        ],
    ),
    (
        "Status Model (State Machine)",
        [
            "Property status treated as state machine: vacant, occupied, unknown, unconfirmed. Unconfirmed is required and represents prompted-but-no-response.",
        ],
    ),
    (
        "Proper Rule Structure (e.g. NYC)",
        [
            "Trigger: address in geofence, stay duration ≥ 30 days. Constraint: hard block booking, max 29 days, warning message.",
            "Document logic: Revocable License template; mandatory clauses (Nature of Relationship, No Exclusive Possession, Utility Prohibition). Risk logic: risk level, GPS liveness at check-in.",
        ],
    ),
    (
        "Core Principle: Record Only",
        [
            "DocuStay records property status and authorization timelines. It does not interpret law, infer outcomes, or act as enforcement. Always recorded status; never fill gaps by guessing; show what was done, when, and by whom.",
        ],
    ),
    (
        "AI Engine (Ingestion & Extraction)",
        [
            "Ingestion: connect to OpenLaws API and LawAtlas; AI scans statute text (e.g. NYC Admin Code § 26-521), identifies keywords.",
            "Extraction: AI extracts time limits and recommends action (e.g. limit stays to 29 days).",
        ],
    ),
    (
        "Shield Mode Toggle",
        [
            "Visible unit-level toggle. ON = enhanced documentation posture; OFF = baseline. Does not mean vacant, enforcement, or guaranteed legal protection. Every toggle change generates an audit event. All four combinations supported: Occupied+Shield ON/OFF, Vacant+Shield ON/OFF.",
        ],
    ),
    (
        "Language Cleanup",
        [
            "Remove or avoid language that declares legal conclusions, labels people, or implies enforcement or criminality. Use neutral, factual state language only.",
        ],
    ),
    (
        "Authoritative Sources (Rule Structure)",
        [
            "Rules reference specific legal sources (e.g. NYC: Admin Code § 26-521, RPAPL § 711, RPA § 713(7), Penal Law § 140.10) with Source ID, statute, and system impact.",
        ],
    ),
    (
        "Archiving, Not Deletion",
        [
            "When units leave portfolios or change management: monitoring stops, history remains, records are archived. Nothing retroactively changes.",
        ],
    ),
    (
        "Token Lifecycle States",
        [
            "Token states: staged, issued, burned, expired, revoked. Evidence-grade: unburned token proves authorization channel was not used; burned proves explicit authorization. States visible in dashboards and evidence exports.",
        ],
    ),
    (
        "Utility Providers",
        [
            "System uses ZIP to identify local utility providers (electric, water, gas, internet) for each property.",
            "Automatically generates Authority Letters to those utilities notifying them DocuStay is the only authorized agent for burn-in codes at those addresses.",
            "Each Utility Provider email lookup",
            "Constructed db with utility provider data"
        ],
    )
]

# --- CONTENT: REMAINING (NOT DONE) ---
NOT_DONE_ITEMS = [
    (
        "Document / Contract Display UI",
        [
            "Fix the document or contract display UI.",
        ],
    ),
    (
        "Stripe Billing Logic (Full Spec)",
        [
            "Onboarding Fee (one-time): charged at initial property upload. Tier by total units in batch: 1–5 → $299 flat; 6–20 → $49/unit; 21–100 → $29/unit; 101–500 → $19/unit; 501–2,000 → $14/unit; 2,001–10,000 → $10/unit; 10,001+ → $7/unit. Single invoice line, non-recurring, tier auto-calculated.",
            "Monthly subscription: $1 baseline ledger fee per unit (recurring) + $10 Shield fee per unit when Shield status = active.",
            "Shield Mode billing: per-unit metered or quantity-based subscription; real-time toggle; immediate proration when Shield turns on or off; $1 baseline always active.",
            "Edge cases: units added mid-cycle → prorate immediately; units removed → stop billing immediately (prorated); Shield toggled mid-cycle → prorate. State-driven; no manual override required.",
        ],
    ),
    (
        "Sign-Up Flow (Individual vs Company)",
        [
            "Initial screen: Are you signing up as Individual Owner, Property Management Company, or Leasing Company?",
            "Individual: First Name, Last Name, Email, Phone, then KYC.",
            "Company: Company Name, Contact Person Name, Email, Phone, Website (optional), Company Type dropdown, then KYC for contact person. KYC non-negotiable before signing.",
        ],
    ),
    (
        "Authority Declaration (Companies)",
        [
            "After KYC, company contact sees: (1) Blanket authority under management agreement → upload management agreement PDF; (2) Separate POAs from each property owner → system sends owner invites after upload. For separate POAs, properties flagged as pending owner verification until POA signed.",
        ],
    ),
    (
        "Master POA Content & Execution",
        [
            "Content: Grantor (verified individual/entity), Agent (DocuStay, Inc.), Properties (all now or hereafter acquired, Exhibit A updatable), Jurisdiction (laws of state where each property is located), Authority (record status, issue/manage guest authorizations, communicate with utilities, document utility status, generate evidence summaries), Duration (until revoked in writing), Revocation (does not erase past records), Exhibit A (property list added after signing).",
            "Execution: POA presented as clear readable document; e-signed with audit trail; stored encrypted in S3 (KMS); hash recorded in audit log. Legal document content needed in app for display; clarify if same document for guest and owner or two different.",
        ],
    ),
    (
        "Property Upload (Manual + CSV)",
        [
            "CSV columns: Address (required), Unit No, City, State, Zip (for jurisdiction), Occupied (YES/NO), Tenant Name (if occupied), Lease Start/End (if occupied), Shield Mode (YES/NO, default NO), Owner Entity ID (for companies).",
            "Processing: each property gets Property Lifecycle Anchor Token; if Occupied=YES burn immediately, record tenant, set Dead-Man Switch from lease end; if Occupied=NO token stays STAGED, status VACANT; Shield YES → toggle ON. For companies with separate POAs: after upload email each owner; properties activate only after owner POA signed. Consider flag/label for properties managed by another company.",
        ],
    ),
    (
        "Token States & User-Facing Labels",
        [
            "STAGED: placeholder not yet used (Gray outline, Staged (Not Used)). BURNED: activated (Solid green, Active). EXPIRED: time-based end (Gray diagonal, Expired). REVOKED: manually terminated (Red outline, Revoked). Dashboard: tenants/owners see STAGED tokens; guests see current stay Active, past Expired; owners see full token history.",
        ],
    ),
    (
        "Guest Authorization Flow",
        [
            "Step 1: Tenant or owner initiates from dashboard; selects staged token; enters guest email or phone; system sends unique link. Step 2: Guest receives link; sees property address (reference) and blank fields; guest fills all their own information and acknowledgment. Step 3: Guest submits; token burns to ACTIVE; guest has dashboard with active authorization. Step 4: Guest dashboard shows current active stay and expired history; only tenants/owners can invite guests. No pre-filling of guest info; token burns only after guest submits.",
        ],
    ),
    (
        "Guest Acknowledgment Template",
        [
            "Title: GUEST ACKNOWLEDGMENT (not agreement/contract). Content: Property, Guest, Authorization Period; acknowledgments (authorized only during period; personal, no sublet/assign; may receive mail, maintenance with consent, pay utilities if applicable; none create tenancy; statute citation from jurisdiction; owner granted DocuStay authority). Statute citation from zip-based jurisdiction lookup. Signed PDF stored; hash in audit log; token burns upon signing.",
        ],
    ),
    (
        "Jurisdiction Logic",
        [
            "Zip-based lookup table: Zip range → State, Statute citations, Max guest stay. Statute text stored verbatim (no AI summarization). Used in guest acknowledgments and evidence summaries.",
        ],
    ),
    (
        "Evidence Summary Views",
        [
            "A) Vacant property (squatter scenario): property, status VACANT, last confirmed, authority chain, jurisdiction + statute citations, utility status with note, timeline, no active guest tokens, no successful /verify attempts.",
            "B) Guest stay ended, no renewal: property, guest, authorization dates, property status occupied by tenant, guest token history ACTIVE then EXPIRED.",
            "D) Guest renewed (guest view): current authorization ACTIVE; past EXPIRED with viewable period.",
        ],
    ),
    (
        "Dead-Man Switch Timing (Full)",
        [
            "Occupied: 48h before lease end first prompt; lease end no auto change; 48h after no action → UNCONFIRMED. Vacant (if owner enables monitoring): prompts at defined intervals; no response → UNCONFIRMED. Silence recorded as evidence.",
        ],
    ),
    (
        "Three Token Layers",
        [
            "Property Lifecycle Anchor Token (tracks occupancy transitions); Tenant Authorization Token (active lawful tenant); Guest Authorization Tokens (multiple). For already-occupied at onboarding: create Lifecycle Anchor, mark Burned-Legacy, attach lease metadata (tenant, lease start/end), store in append-only log.",
        ],
    ),
    (
        "Burn / Expire / Revoke Definitions",
        [
            "Burn: token permanently linked to verified identity and timestamp; no longer staged. Expire: automatic state change at defined time (lease end, guest stay end). Revoked: manual action by Owner or Authorized Agent; logged with timestamp and identity.",
        ],
    ),
    (
        "/verify Portal",
        [
            "Dedicated page at docustay.online/verify. Required: Token ID, Property Address. Optional: Name, Phone. Address as second-factor to prevent token guessing. Log every attempt (success or failure); failed/mismatched = Identity Conflict. User-agnostic (tenant, owner, agent, law enforcement, any third party). Purpose: answer whether there is an active authorization for this address and token. Display: verified authority summary, Master POA summary, current property status, active/expired token states, live timestamp, expandable audit timeline. Logging does NOT automatically notify owner or escalate; purpose is timeline integrity. Burn tokens only on success. System works even if /verify is never used; absence of verification is meaningful.",
        ],
    ),
    (
        "GuestGuard (Self-Complete Only)",
        [
            "Only the guest may complete the flow (sign, acknowledge, provide own info). No proxy-sign or completion by owner/tenant. Enforcement: unique identity-bound invite link; SMS or email verification; device/IP logging; owner-device match detection. If proxy-sign detected: token locked, audit event, guest must authenticate directly. Exception: only verified legal POA for guest (e.g. minor/incapacitated) with upload and verification. GuestGuard is baseline for all units, not a paid toggle.",
        ],
    ),
    (
        "Jurisdictional POA Wrap",
        [
            "One Master POA per owner entity. System produces dynamic authority package: Master POA + jurisdiction-specific laws (zip-based lookup) + property identifier (e.g. Tax ID/APN). Template merge (no AI legal interpretation). Dedicated link /property/:id/authority generated by system; owner or agent may share. When opened: verified owner identity, Master POA summary, scope, current property status, statute citations, live timestamp, link to full evidence timeline. View is live and reflects real-time state.",
        ],
    ),
    (
        "Evidence View & Exports",
        [
            "Dedicated route /property/:id/evidence. Access: Owner full; Authorized Agent portfolio-level; Law enforcement via secure time-limited link. Content: live timestamp, status summary, Master POA summary, Lifecycle Anchor timeline, tenant token history, guest token history, /verify attempts, audit log entries. Printable PDF: timestamp, verification hash footer, verification link to live record. Read-only, shareable, live; summary first, expandable to full timelines. Records append-only, never deleted.",
        ],
    ),
    (
        "Enhanced Guest Guard ($1/unit Layer)",
        [
            "DocuStay Verify: guest verifies via name + phone; Digital Fingerprint linked to legal acknowledgment (forensic proof of who signed what). Expanded clauses: Mail/Package (delivery ≠ residency), Labor/Improvements (fixing things ≠ tenant rights), Purpose of Presence (transient), Live countdown timer that at zero flips guest status to EXPIRED/TRESPASSER in police Live-Share view.",
        ],
    ),
    (
        "Forensic Fraud Capture (Identity Conflict Logging)",
        [
            "Immutable audit trail of failed access attempts. If someone tries wrong name/phone on Utility Token or Guest Agreement: record Unauthorized Identity Attempt (e.g. Phone -XXXX) at timestamp. Evidence if squatter later claims they were invited.",
        ],
    ),
    (
        "One-Click Shield Mode Across Multiple Properties",
        [
            "Ability to activate Shield Mode in one action across multiple selected properties.",
        ],
    ),
    (
        "Batch Operations for Dead Man's Switch",
        [
            "Batch operations for Dead Man's Switch settings across multiple units.",
        ],
    ),
    (
        "Licensee Holdover Packet (Court Defense)",
        [
            "If dispute: system generates packet with Rule Log (system blocked booking >29 days to prevent tenancy), Statute Citation (e.g. NYC Admin Code § 26-521), Signed Agreement (Revocable License signature), GPS Log (guest checked in at location, confirming receipt of License). Proves no tenancy was intended or legally created.",
        ],
    ),
    (
        "Dashboards Expose Gaps",
        [
            "Surface unconfirmed units, pending manual steps, token states; allow filtering across portfolios; avoid language that implies legal outcomes. Goal is clarity, not accusation. Control plane for declared posture and recorded state.",
        ],
    ),
    (
        "Human Verification for Rules (Safety Lock)",
        [
            "AI creates Draft Rule; does not go live. Legal admin (or DocuStay team) gets notification; sees AI extraction side-by-side with law text; clicks APPROVE to activate rule in database. Critical for patentability and liability.",
        ],
    ),
    (
        "Runtime Resolver (Booking Guardrail)",
        [
            "When guest selects stay in jurisdiction (e.g. NYC) with duration exceeding max (e.g. 35 days vs 29): system auto-rejects date selection with message citing local law (e.g. NYC Local Law § 26-521, temporary stays cannot exceed 29 days).",
        ],
    ),
    (
        "Authorized Agent Role",
        [
            "Separate role from Owner of Record: identity verified; can manage property status, issue tokens, generate evidence links; cannot revoke Master POA or delete portfolio. If Property Manager signs instead of Owner, they must certify authority under management agreement to delegate to DocuStay; certification logged and preserved.",
        ],
    ),
    (
        "Manual Document Upload Without Biometric",
        [
            "Manual document upload without biometric validation is insufficient. Manual review only as fallback. Verified identity record tied to Master POA signer.",
        ],
    ),
    (
        "Live-Share Link (3-Second Rule for Police)",
        [
            "Mobile-optimized evidence page for police at scene. In 3 seconds: property address, current status (e.g. Protected-Vacant), applicable local statute (e.g. RCW 9A.52.105), Certificate of Authenticity citing Master POA and Rule 803(6). Live, real-time verification (not static evidence package). Clarify: will evidence page be sent to owner? When guest is overstaying or at another property?",
        ],
    ),
    (
        "Gap Filter",
        [
            "Filter to find vulnerable units (e.g. VACANT with Shield Mode OFF).",
        ],
    ),
    (
        "Relationship: Status, Shield, GuestGuard",
        [
            "Three independent dimensions on dashboard. Status = recorded state of unit. Shield Mode = documentation posture chosen. GuestGuard = whether guest authorizations are recorded (baseline when used). Example row: Unit 204B, Status VACANT, Status Certainty CONFIRMED, Shield Mode ON, GuestGuard Activity NONE, Token State STAGED, Last Confirmation. No nesting or implication between them.",
        ],
    ),
    (
        "Evidence View & Printable Summary (Requirement)",
        [
            "Read-only, shareable, live evidence view: summary first (status, posture, timestamp), expandable to full timelines, printable as clean PDF, reflect live data. How third parties understand the record quickly.",
        ],
    ),
]

# --- CONTENT: UNCLEAR REQUIREMENTS (Need clarification) ---
UNCLEAR_ITEMS = [
    (
        "Stripe verification fail case",
        [
            "It is unclear how to manually verify the user when Stripe identity verification fails.",
        ],
    ),
    (
        "Utility provider data verification",
        [
            "It is unclear how to manually verify utility provider data, as there is no single source of truth.",
        ],
    ),
]


def build_pdf(buffer):
    styles = getSampleStyleSheet()
    styles = build_styles(styles)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    story = []

    # Title
    story.append(
        Paragraph(
            escape("DocuStay Requirements — Status Overview"),
            styles["DocTitle"],
        )
    )
    story.append(
        Paragraph(
            escape(f"Generated: {datetime.now().strftime('%B %d, %Y')}"),
            styles["DocNote"],
        )
    )
    story.append(
        Paragraph(
            escape(
                "This document consolidates all product and legal requirements into a single list, "
                "marked as Completed (Done) or Remaining (Not Done). Overlapping or later-added items have been merged; nothing is omitted."
            ),
            styles["DocBody"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Section: Completed
    story.append(
        Paragraph(
            escape("1. Completed Requirements (Done)"),
            styles["SectionHeading"],
        )
    )
    for i, (title, bullets) in enumerate(DONE_ITEMS, 1):
        story.append(
            Paragraph(
                escape(f"{i}. {title}"),
                styles["SubHeading"],
            )
        )
        for b in bullets:
            story.append(
                Paragraph(
                    escape(f"• {b}"),
                    styles["DocBullet"],
                )
            )
        story.append(Spacer(1, 0.08 * inch))

    story.append(PageBreak())

    # Section: Remaining
    story.append(
        Paragraph(
            escape("2. Remaining Requirements (Not Done)"),
            styles["SectionHeading"],
        )
    )
    for i, (title, bullets) in enumerate(NOT_DONE_ITEMS, 1):
        story.append(
            Paragraph(
                escape(f"{i}. {title}"),
                styles["SubHeading"],
            )
        )
        for b in bullets:
            story.append(
                Paragraph(
                    escape(f"• {b}"),
                    styles["DocBullet"],
                )
            )
        story.append(Spacer(1, 0.08 * inch))

    # Section: Unclear requirements
    story.append(PageBreak())
    story.append(
        Paragraph(
            escape("3. Unclear Requirements (Need Clarification)"),
            styles["UnclearHeading"],
        )
    )
    story.append(
        Paragraph(
            escape(
                "The following items require product or process clarification before implementation can be finalized."
            ),
            styles["DocBody"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))
    for i, (title, bullets) in enumerate(UNCLEAR_ITEMS, 1):
        story.append(
            Paragraph(
                escape(f"{i}. {title}"),
                styles["SubHeading"],
            )
        )
        for b in bullets:
            story.append(
                Paragraph(
                    escape(f"• {b}"),
                    styles["DocBullet"],
                )
            )
        story.append(Spacer(1, 0.08 * inch))

    doc.build(story)


def main():
    project_root = Path(__file__).resolve().parent.parent
    out_dir = project_root / "docs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "Docustay_Requirements_Status.pdf"

    buffer = BytesIO()
    build_pdf(buffer)
    with open(out_path, "wb") as f:
        f.write(buffer.getvalue())

    print(f"PDF written to: {out_path}")


if __name__ == "__main__":
    main()
