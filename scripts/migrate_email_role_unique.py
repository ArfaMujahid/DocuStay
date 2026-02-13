"""
Replace any users.email-only UNIQUE with UNIQUE (email, role) so the same email
can be used for both an owner account and a guest account.
Only (email, role) is unique; email alone is not.
For a NEW database: not needed; User model has UniqueConstraint("email", "role").
Run once on an EXISTING DB: python scripts/migrate_email_role_unique.py (from project root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine


def main():
    with engine.begin() as conn:
        # Unique constraints on users
        r = conn.execute(text("""
            SELECT c.conname, c.conkey
            FROM pg_constraint c
            WHERE c.conrelid = 'users'::regclass AND c.contype = 'u'
        """))
        unique_constraints = [(row[0], row[1]) for row in r]
        constraint_names = [c[0] for c in unique_constraints]

        # Column attnum for email and role
        attrs = conn.execute(text("""
            SELECT a.attname, a.attnum FROM pg_attribute a
            WHERE a.attrelid = 'users'::regclass AND a.attnum > 0 AND NOT a.attisdropped
        """))
        name_to_num = {row[0]: row[1] for row in attrs}
        email_num = name_to_num.get("email")

        # Drop any unique constraint that is on email only (so we can have same email for owner and guest)
        for conname, conkey in unique_constraints:
            if conkey is None or len(conkey) == 0:
                continue
            if conname == "uq_users_email_role":
                continue
            if len(conkey) == 1 and email_num is not None and conkey[0] == email_num:
                conn.execute(text(f'ALTER TABLE users DROP CONSTRAINT IF EXISTS "{conname}"'))
                print(f"  dropped email-only constraint: {conname}")
                break
        else:
            # No constraint matched; drop unique index on email if it exists (e.g. ix_users_email)
            for idx_name in ["ix_users_email", "users_email_key"]:
                conn.execute(text(f'DROP INDEX IF EXISTS "{idx_name}"'))
                print(f"  dropped index (if existed): {idx_name}")

        # Ensure (email, role) unique exists
        if "uq_users_email_role" not in constraint_names:
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT uq_users_email_role UNIQUE (email, role)"))
            print("  added constraint: uq_users_email_role")
        else:
            print("  uq_users_email_role already exists")

    print("Done. Only (email, role) is unique; email alone is not.")


if __name__ == "__main__":
    main()
