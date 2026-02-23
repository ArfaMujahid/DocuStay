"""
List all user emails from the database.
Run from project root: python scripts/list_user_emails.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))


def main():
    from app.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("No users in database.")
            return
        print(f"Total users: {len(users)}\n")
        for u in users:
            role = u.role.value if u.role else "?"
            print(f"  {u.email} (role: {role})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
