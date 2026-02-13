"""
Trigger Shield Mode and Dead Man's Switch for testing on a specific property.

Finds "Test Property 2" (or property matching --name/--address), sets its active stay's
end date to TODAY, then runs the stay timer job. This will:
  - Activate Shield Mode (last day of stay)
  - Send Dead Man's Switch "lease ends today" alert (if DMS enabled on stay)
  - Create audit log entries

Usage (from project root):
  python scripts/trigger_shield_and_dms_test.py
  python scripts/trigger_shield_and_dms_test.py --name "Test Property 2"
  python scripts/trigger_shield_and_dms_test.py --property-id 5

After running, refresh the owner dashboard to see Shield Mode ON and check Logs.
"""
import os
import sys
import argparse
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.stay import Stay
from app.models.owner import Property
from app.services.stay_timer import run_dead_mans_switch_job


def main():
    parser = argparse.ArgumentParser(description="Trigger Shield Mode + DMS for testing")
    parser.add_argument("--name", type=str, default="Test Property 2", help="Property name to find")
    parser.add_argument("--property-id", type=int, default=None, help="Or specify property ID directly")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be done")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        if args.property_id:
            prop = db.query(Property).filter(Property.id == args.property_id, Property.deleted_at.is_(None)).first()
        else:
            prop = db.query(Property).filter(
                Property.name.ilike(f"%{args.name}%"),
                Property.deleted_at.is_(None),
            ).first()

        if not prop:
            print("No property found.")
            if not args.property_id:
                print(f'  Tried name like "%{args.name}%". Use --property-id ID if needed.')
            return 1

        stay = (
            db.query(Stay)
            .filter(
                Stay.property_id == prop.id,
                Stay.checked_out_at.is_(None),
                Stay.cancelled_at.is_(None),
            )
            .first()
        )

        if not stay:
            print(f"Property '{prop.name or prop.id}' has no active stay (all checked out or cancelled).")
            return 1

        today = date.today()
        original_end = stay.stay_end_date
        dms_on = getattr(stay, "dead_mans_switch_enabled", 0) == 1

        print(f"Property: {prop.name or prop.id} (id={prop.id})")
        print(f"Stay id={stay.id}, end_date={original_end} -> setting to {today}")
        print(f"Dead Man's Switch on this stay: {'yes' if dms_on else 'no'}")
        if args.dry_run:
            print("Dry run: not modifying DB or running job.")
            return 0

        stay.stay_end_date = today
        if not dms_on:
            setattr(stay, "dead_mans_switch_enabled", 1)
            setattr(stay, "dead_mans_switch_alert_email", 1)
            print("  (Enabled DMS on this stay for testing.)")
        db.add(stay)
        db.commit()

        print("Running stay timer job (Shield Mode + DMS)...")
        run_dead_mans_switch_job(db)

        print("Done. Refresh the owner dashboard:")
        print("  - Shield Mode should show ON for this property.")
        print("  - Logs tab should show 'Shield Mode activated' and/or 'Dead Man's Switch: urgent – lease ends today'.")
        print(f"  - To re-test later, set stay {stay.id} end_date back to {original_end} in DB if needed.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main() or 0)
