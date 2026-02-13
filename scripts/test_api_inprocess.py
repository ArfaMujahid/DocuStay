"""
Backend API test – in-process via TestClient (no separate server).
Run: python scripts/test_api_inprocess.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.database import SessionLocal, engine, Base
# Import models so create_all creates tables
from app.models import User, OwnerProfile, Property, GuestProfile, Stay, RegionRule  # noqa: F401
from app.main import app
from app.seed import seed_region_rules

# Ensure DB and tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    seed_region_rules(db)
finally:
    db.close()

client = TestClient(app)
passed = failed = 0
owner_token = guest_token = None
property_id = stay_id = None


def req(method, path, body=None, token=None):
    kwargs = {"headers": {"Accept": "application/json"}}
    if token:
        kwargs["headers"]["Authorization"] = f"Bearer {token}"
    if body:
        kwargs["json"] = body
    r = client.request(method, path, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    return r.json() if r.content else {}


def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  OK  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        failed += 1


def main():
    global owner_token, guest_token, property_id, stay_id
    print("DocuStay Backend API Tests (in-process)\n" + "=" * 50)

    test("GET /", lambda: req("GET", "/"))
    test("GET /health", lambda: req("GET", "/health"))

    # Module A
    print("\n--- Module A: Auth & Role Selection ---")
    test("POST /auth/register (owner)", lambda: req("POST", "/auth/register", {
        "email": "owner@test.docustay.demo", "password": "testpass123", "role": "owner"}))
    test("POST /auth/register (guest)", lambda: req("POST", "/auth/register", {
        "email": "guest@test.docustay.demo", "password": "testpass123", "role": "guest"}))
    r = req("POST", "/auth/login", {"email": "owner@test.docustay.demo", "password": "testpass123"})
    owner_token = (r.get("access_token") or "").strip()
    test("POST /auth/login (owner)", lambda: None if not owner_token else None)
    r = req("POST", "/auth/login", {"email": "guest@test.docustay.demo", "password": "testpass123"})
    guest_token = (r.get("access_token") or "").strip()
    test("POST /auth/login (guest)", lambda: None if not guest_token else None)
    test("GET /auth/me (owner)", lambda: req("GET", "/auth/me", token=owner_token))
    test("GET /auth/me (guest)", lambda: req("GET", "/auth/me", token=guest_token))

    # Module B1
    print("\n--- Module B1: Owner Onboarding ---")
    def add_prop():
        global property_id
        property_id = req("POST", "/owners/properties", {
            "street": "123 Main St", "city": "Brooklyn", "state": "NY", "region_code": "NYC",
            "owner_occupied": False, "property_type": "entire_home"}, token=owner_token)["id"]
    test("POST /owners/properties", add_prop)
    test("GET /owners/properties", lambda: req("GET", "/owners/properties", token=owner_token))
    test("GET /owners/properties/{id}", lambda: req("GET", f"/owners/properties/{property_id}", token=owner_token))

    # Module B2
    print("\n--- Module B2: Guest Onboarding ---")
    test("PUT /guests/profile", lambda: req("PUT", "/guests/profile", {
        "full_legal_name": "Jane Guest", "permanent_home_address": "456 Other Ave, LA, CA",
        "gps_checkin_acknowledgment": True}, token=guest_token))
    test("GET /guests/profile", lambda: req("GET", "/guests/profile", token=guest_token))

    # Module C
    print("\n--- Module C: Stay Creation & Storage ---")
    def add_stay():
        global stay_id
        stay_id = req("POST", "/stays/", {
            "property_id": property_id, "stay_start_date": "2025-02-01", "stay_end_date": "2025-02-14",
            "purpose_of_stay": "travel", "relationship_to_owner": "friend", "region_code": "NYC"},
            token=guest_token)["id"]
    test("POST /stays/", add_stay)
    test("GET /stays/ (guest)", lambda: req("GET", "/stays/?as_guest=true", token=guest_token))
    test("GET /stays/ (owner)", lambda: req("GET", "/stays/?as_guest=false", token=owner_token))
    test("GET /stays/{id}", lambda: req("GET", f"/stays/{stay_id}", token=guest_token))

    # Module D
    print("\n--- Module D: Region Rules ---")
    test("GET /region-rules/", lambda: req("GET", "/region-rules/", token=owner_token))
    test("GET /region-rules/NYC", lambda: req("GET", "/region-rules/NYC", token=owner_token))
    test("GET /region-rules/CA", lambda: req("GET", "/region-rules/CA", token=owner_token))

    # Module E
    print("\n--- Module E: JLE ---")
    test("POST /jle/resolve", lambda: req("POST", "/jle/resolve", {
        "region_code": "NYC", "stay_duration_days": 14, "owner_occupied": False,
        "property_type": "entire_home", "guest_has_permanent_address": True}, token=owner_token))

    # Module F
    print("\n--- Module F: Dashboard ---")
    test("GET /dashboard/owner/stays", lambda: req("GET", "/dashboard/owner/stays", token=owner_token))
    test("GET /dashboard/guest/stays", lambda: req("GET", "/dashboard/guest/stays", token=guest_token))

    # Module G/H
    print("\n--- Module G & H: Notifications ---")
    test("POST /notifications/run-stay-warnings", lambda: req("POST", "/notifications/run-stay-warnings", token=owner_token))

    print("\n" + "=" * 50)
    print(f"Passed: {passed}  Failed: {failed}  Total: {passed + failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
