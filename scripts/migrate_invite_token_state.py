"""
Add token_state to invitations and invitation_id to stays; backfill where possible.
Run from project root: python scripts/migrate_invite_token_state.py

Invite token states: STAGED (created), BURNED (accepted + MoA signed), EXPIRED (stay ended/checked out), REVOKED (cancelled).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import SessionLocal, engine
    from app.models.invitation import Invitation
    from app.models.stay import Stay
    from sqlalchemy import text

    # Add columns if not present (PostgreSQL: IF NOT EXISTS; SQLite: try and ignore duplicate)
    with engine.connect() as conn:
        for stmt, name in [
            ("ALTER TABLE invitations ADD COLUMN token_state VARCHAR(20) DEFAULT 'STAGED'", "invitations.token_state"),
            ("ALTER TABLE stays ADD COLUMN invitation_id INTEGER", "stays.invitation_id"),
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"  {name}: added")
            except Exception as e:
                err = str(e).lower()
                if "duplicate" in err or "already exists" in err or "exist" in err:
                    print(f"  {name}: already exists")
                else:
                    # PostgreSQL: try with IF NOT EXISTS for invitations
                    if "token_state" in name:
                        try:
                            conn.execute(text("ALTER TABLE invitations ADD COLUMN IF NOT EXISTS token_state VARCHAR(20) DEFAULT 'STAGED'"))
                            conn.commit()
                            print(f"  {name}: ok")
                        except Exception as e2:
                            print(f"  {name}: {e2}")
                            raise
                    else:
                        print(f"  {name}: {e}")
                        raise

    db = SessionLocal()
    try:
        # Backfill invitation token_state from status (accepted -> BURNED, cancelled -> REVOKED)
        invs = db.query(Invitation).all()
        updated = 0
        for inv in invs:
            current = getattr(inv, "token_state", None) or ""
            if inv.status == "accepted" and current != "BURNED":
                inv.token_state = "BURNED"
                updated += 1
            elif inv.status == "cancelled" and current != "REVOKED":
                inv.token_state = "REVOKED"
                updated += 1
            elif current not in ("STAGED", "BURNED", "EXPIRED", "REVOKED"):
                inv.token_state = "STAGED"
                updated += 1
        db.commit()
        print(f"  Backfilled token_state for {updated} invitations.")

        # Optionally link stays to invitations (accepted invite with same property, dates, owner)
        stays_without_inv = db.query(Stay).filter(Stay.invitation_id.is_(None)).all()
        linked = 0
        for stay in stays_without_inv:
            inv = (
                db.query(Invitation)
                .filter(
                    Invitation.property_id == stay.property_id,
                    Invitation.owner_id == stay.owner_id,
                    Invitation.stay_start_date == stay.stay_start_date,
                    Invitation.stay_end_date == stay.stay_end_date,
                    Invitation.status == "accepted",
                )
                .first()
            )
            if inv:
                stay.invitation_id = inv.id
                linked += 1
        db.commit()
        print(f"  Linked {linked} stays to invitations.")
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    main()
