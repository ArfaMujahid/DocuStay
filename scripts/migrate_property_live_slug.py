"""
Add live_slug column to properties and backfill for existing rows.
Run from project root: python scripts/migrate_property_live_slug.py
"""
import os
import secrets
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import SessionLocal
    from app.models.owner import Property
    from sqlalchemy import text

    engine = None
    try:
        from app.database import engine
    except Exception:
        pass
    if engine is not None:
        with engine.connect() as conn:
            try:
                conn.execute(text(
                    "ALTER TABLE properties ADD COLUMN IF NOT EXISTS live_slug VARCHAR(32)"
                ))
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_properties_live_slug ON properties (live_slug)"
                ))
                conn.commit()
                print("  properties.live_slug column and index: ok")
            except Exception as e:
                print(f"  properties.live_slug: {e}")
                raise

    db = SessionLocal()
    try:
        existing_slugs = {r[0] for r in db.query(Property.live_slug).filter(Property.live_slug.isnot(None)).all()}
        props = db.query(Property).filter(Property.live_slug.is_(None)).all()
        for prop in props:
            for _ in range(15):
                slug = secrets.token_urlsafe(12).replace("+", "-").replace("/", "_")[:24]
                if slug not in existing_slugs:
                    prop.live_slug = slug
                    existing_slugs.add(slug)
                    break
            else:
                prop.live_slug = secrets.token_urlsafe(8).replace("+", "-").replace("/", "_")[:20] + "-" + str(prop.id)
                existing_slugs.add(prop.live_slug)
        db.commit()
        print(f"  Backfilled live_slug for {len(props)} properties.")
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    main()
