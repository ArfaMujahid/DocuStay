"""
Add Dead Man's Switch columns to invitations and stays tables.
Run once on an EXISTING DB: python scripts/migrate_dead_mans_switch.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine


def main():
    insp = inspect(engine)
    inv_cols = {c["name"] for c in insp.get_columns("invitations")}
    stay_cols = {c["name"] for c in insp.get_columns("stays")}

    with engine.begin() as conn:
        for col, default in [
            ("dead_mans_switch_enabled", 0),
            ("dead_mans_switch_alert_email", 1),
            ("dead_mans_switch_alert_sms", 0),
            ("dead_mans_switch_alert_dashboard", 1),
            ("dead_mans_switch_alert_phone", 0),
        ]:
            if col not in inv_cols:
                conn.execute(text(f'ALTER TABLE invitations ADD COLUMN "{col}" INTEGER NOT NULL DEFAULT {default}'))
                print(f"  added: invitations.{col}")
            else:
                print(f"  skip (exists): invitations.{col}")

        for col, default in [
            ("dead_mans_switch_enabled", 0),
            ("dead_mans_switch_alert_email", 1),
            ("dead_mans_switch_alert_sms", 0),
            ("dead_mans_switch_alert_dashboard", 1),
            ("dead_mans_switch_alert_phone", 0),
        ]:
            if col not in stay_cols:
                conn.execute(text(f'ALTER TABLE stays ADD COLUMN "{col}" INTEGER NOT NULL DEFAULT {default}'))
                print(f"  added: stays.{col}")
            else:
                print(f"  skip (exists): stays.{col}")

        if "dead_mans_switch_triggered_at" not in stay_cols:
            conn.execute(text('ALTER TABLE stays ADD COLUMN "dead_mans_switch_triggered_at" TIMESTAMP WITH TIME ZONE'))
            print("  added: stays.dead_mans_switch_triggered_at")
        else:
            print("  skip (exists): stays.dead_mans_switch_triggered_at")

    print("Done.")


if __name__ == "__main__":
    main()
