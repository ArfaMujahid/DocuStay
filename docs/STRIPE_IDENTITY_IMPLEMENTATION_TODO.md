# Stripe Identity & Owner/Manager Onboarding – Implementation Todo

This document lists what to implement and in what order to meet the client requirements for **identity verification** and **professional onboarding** (Owner of Record / Authorized Agent).

---

## Client requirements (summary)

- **Who:** Owners and Property Managers only (not guests).
- **What:** Third-party KYC identity verification (Stripe Identity) with:
  - Government-issued ID upload
  - OCR data extraction
  - Selfie + liveness verification
  - Identity match validation
- **When:** After account creation → **before** signing Master POA → **before** adding any property → **before** accessing operational dashboard.
- **Roles:**
  - **Owner of Record:** Signs Master POA, can revoke POA, can transfer portfolio.
  - **Authorized Agent:** Must also be identity verified; can manage property, issue tokens, generate evidence; cannot revoke Master POA or delete portfolio. If they sign instead of Owner, they certify authority under their management agreement (certification logged).

---

## Env & config (done)

- [x] Write Stripe keys and Identity settings to `.env` and `.env.example`.
- [x] Add Stripe settings to `app/config.py` (secret, publishable, flow ID, return URL).
- [x] Add `VITE_STRIPE_PUBLISHABLE_KEY` to frontend `.env.local` for Stripe.js.

**Note:** Return URL is set to `http://localhost:3000/#onboarding/identity-complete` so the SPA (hash routing) can handle the redirect. If you use path-based routing later, set `STRIPE_IDENTITY_RETURN_URL` to that path in Stripe Dashboard and in `.env`.

---

## Implementation order

### 1. Database: identity verification state

- [ ] Add to **User** (or new table) for owners:
  - `identity_verified_at` (datetime, nullable) – set when Stripe verification succeeds.
  - `stripe_verification_session_id` (string, nullable) – link to Stripe Identity session for audit.
- [ ] Optional: add `onboarding_step` or `identity_verification_status` if you want explicit steps (e.g. `pending_identity` → `identity_verified` → `poa_signed`).
- [ ] Migration script or `create_all` update.

**Purpose:** Block POA, property add, and dashboard until `identity_verified_at` is set.

---

### 2. Backend: Stripe Identity API

- [ ] Install `stripe` in backend (e.g. `pip install stripe`).
- [ ] **Create verification session endpoint** (e.g. `POST /auth/identity/verification-session` or under `/onboarding`):
  - Require authenticated owner (or temporary token for post-signup flow).
  - Call Stripe API: create [VerificationSession](https://docs.stripe.com/identity/verification-sessions) with:
    - `type: "document"` (or use Flow ID if your Stripe account uses Verification Flows).
    - `return_url`: from config (`STRIPE_IDENTITY_RETURN_URL`).
    - `metadata` or `client_reference_id`: current user id.
  - Return `client_secret` (and optionally `url`) to the frontend.
- [ ] **Return URL handler** (e.g. `GET /auth/identity/complete` or frontend-only):
  - If backend: receive redirect with `session_id` (or read from query), verify session with Stripe, then set `identity_verified_at` and `stripe_verification_session_id` for the user.
  - If frontend-only: frontend page `#onboarding/identity-complete` reads `session_id` from query, calls backend `POST /auth/identity/confirm` with session id; backend verifies with Stripe and marks user verified.
- [ ] **Stripe webhook** (optional but recommended): listen for `identity.verification_session.verified` to mark user verified even if return redirect fails; more reliable.

**Purpose:** Allow frontend to start verification and reliably persist “verified” state.

---

### 3. Backend: enforce “identity before POA / property / dashboard”

- [ ] **Guards/dependencies:**
  - For owner-only routes that must run only after identity verification: check `identity_verified_at`; if missing, return `403` with a clear message (e.g. “Complete identity verification first”) and a link/code for the frontend to show the onboarding identity step.
- [ ] Apply guards to:
  - Master POA sign (e.g. agreements: sign POA only if identity verified).
  - Add property (e.g. `POST /properties` or equivalent).
  - Dashboard (e.g. `/dashboard/owner/*` or equivalent).
- [ ] Ensure **registration flow** does not allow bypass: e.g. after account creation, owner cannot access dashboard or POA until identity is done.

**Purpose:** Enforce “no POA, no property, no dashboard” until identity is verified.

---

### 4. Frontend: onboarding flow reorder

Current flow: Register (form + Master POA) → verify email → dashboard.

Target flow: **Account creation** → **Identity verification** → **Master POA** → (email verify if needed) → **Dashboard**.

- [ ] **Split owner registration:**
  - **Step 1 – Create account only:** Collect email, password, name, contact, terms. Do **not** require POA yet. Create user with `identity_verified_at = null`.
  - After success: redirect to identity verification step (or show it in same wizard).
- [ ] **Step 2 – Identity verification:**
  - New page/route, e.g. `#onboarding/identity` (or `#register/identity`).
  - Call backend to create Stripe VerificationSession; open Stripe’s verification UI (redirect or embedded) using `client_secret`.
  - On return: user lands on `#onboarding/identity-complete` (or path you set in Stripe).
- [ ] **Step 3 – Identity complete page:**
  - New route: `#onboarding/identity-complete`. Read `session_id` from URL if Stripe appends it; call backend to confirm and set `identity_verified_at`.
  - Then redirect to **Master POA** step.
- [ ] **Step 4 – Master POA:** Existing POA flow (e.g. open POA modal, sign, get `poa_signature_id`), then link POA to user (e.g. existing or new endpoint that accepts `poa_signature_id` for this user).
- [ ] **Step 5 – Email verification** (if you keep it): same as today after POA.
- [ ] **Step 6 – Dashboard:** Only after identity + POA (and email if required); hide dashboard until then.

**Purpose:** Implement the exact trigger order: account → identity → POA → property/dashboard.

---

### 5. Frontend: dashboard and property guards

- [ ] When owner loads dashboard or “Add property”, backend already returns 403 if not identity-verified; frontend should:
  - Detect 403 + “identity verification required” (e.g. by message or code).
  - Redirect to onboarding identity step (e.g. `#onboarding/identity`) and show a clear message.
- [ ] Optional: on app load, if user is owner and `identity_verified_at` is false (from `/me` or user payload), redirect to identity step before showing dashboard.

**Purpose:** Smooth UX so users are always sent to the right step.

---

### 6. Authorized Agent vs Owner of Record (phase 2)

- [ ] **Data model:** Add role or type for owner accounts, e.g. `owner_type`: `owner_of_record` | `authorized_agent`.
- [ ] **Certification:** When an Authorized Agent signs (e.g. Master POA or a separate “authority” doc), add a checkbox/statement: “I certify I have authority under my management agreement to delegate documentation authority to DocuStay.” Store acceptance (and timestamp) in DB and in audit log.
- [ ] **Permissions:** Enforce in backend:
  - Owner of Record: can revoke Master POA, can transfer/delete portfolio.
  - Authorized Agent: can manage property, issue tokens, generate evidence; cannot revoke POA or delete portfolio.
- [ ] **UI:** Registration or onboarding: choose “I am the Owner of Record” vs “I am an Authorized Agent (e.g. property manager)”; show certification text for Agent.

**Purpose:** Fulfill role distinction and certification requirement.

---

### 7. Optional but recommended

- [ ] **Stripe webhook:** `identity.verification_session.verified` (and optionally `verified` with session id) to set `identity_verified_at` and `stripe_verification_session_id`; reduces dependency on redirect.
- [ ] **Idempotency:** When creating VerificationSessions, use an idempotency key (e.g. user_id + “identity”) to avoid duplicate sessions.
- [ ] **Return URL in Stripe Dashboard:** In Stripe Dashboard → Identity → your flow, set the same return URL as in `.env` (e.g. `http://localhost:3000/#onboarding/identity-complete`).

---

## What is required beyond what you have

- **Backend:** Stripe SDK, new endpoints (create session, confirm/complete), guards on POA/property/dashboard, and DB fields for identity verification.
- **Frontend:** New routes/pages (identity step, identity-complete), reordered registration flow (account → identity → POA), and handling of 403 from backend to redirect to identity step.
- **Stripe Dashboard:** Ensure your Identity Verification Flow (Flow ID in `.env`) has the correct return URL and that document + selfie/liveness checks are enabled to meet “government ID + OCR + selfie + match”.
- **Authorized Agent:** Role + certification + permission checks (can be phase 2 after basic identity works).

---

## File reference (suggested)

| Area              | Files to touch |
|-------------------|----------------|
| Env               | `.env`, `.env.example`, `frontend/.env.local` (done) |
| Config            | `app/config.py` (done) |
| DB                | `app/models/user.py` (or new `owner_identity_verification` table), migration |
| Stripe API        | New router e.g. `app/routers/identity.py` or under `auth.py` |
| Guards            | `app/dependencies.py` or route dependencies |
| POA / property    | `app/routers/agreements.py`, `app/routers/owners.py`, `app/routers/dashboard.py` |
| Frontend flow     | `frontend/App.tsx`, `frontend/pages/Auth/RegisterOwner.tsx`, new `OnboardingIdentity.tsx`, `OnboardingIdentityComplete.tsx` |
| API client        | `frontend/services/api.ts` (identity endpoints) |

---

*Last updated: implementation plan for Stripe Identity and owner/manager onboarding.*
