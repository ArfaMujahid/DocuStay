"""
Add billing columns to owner_profiles if they do not exist.
For existing databases created before onboarding fee was added.
Run from project root: python scripts/migrate_billing_columns.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        for col, typ in [
            ("stripe_customer_id", "VARCHAR(255)"),
            ("stripe_subscription_id", "VARCHAR(255)"),
            ("stripe_subscription_baseline_item_id", "VARCHAR(255)"),
            ("stripe_subscription_shield_item_id", "VARCHAR(255)"),
            ("onboarding_billing_completed_at", "TIMESTAMP WITH TIME ZONE"),
            ("onboarding_billing_unit_count", "INTEGER"),
            ("onboarding_invoice_paid_at", "TIMESTAMP WITH TIME ZONE"),
        ]:
            try:
                conn.execute(text(
                    f"ALTER TABLE owner_profiles ADD COLUMN IF NOT EXISTS {col} {typ}"
                ))
                print(f"  owner_profiles.{col}: ok")
            except Exception as e:
                print(f"  owner_profiles.{col}: {e}")
        conn.commit()
    print("Done.")


if __name__ == "__main__":
    main()
