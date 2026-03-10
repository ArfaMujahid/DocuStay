"""Generate a JWT token for the test user so we can call the API directly."""
from app.database import SessionLocal
from app.models.user import User
from app.services.auth import create_access_token

db = SessionLocal()
user = db.query(User).filter(User.email == "wiyoh65359@daerdy.com").first()
if user:
    token = create_access_token({"sub": str(user.id), "role": user.role.value if hasattr(user.role, "value") else user.role})
    print("TOKEN:", token)
    print("USER ID:", user.id, "ROLE:", user.role)
else:
    print("User not found")
db.close()
