"""Shared dependencies: DB session, current user."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth import decode_token_with_error

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_str = (credentials.credentials or "").strip()
    payload, _ = decode_token_with_error(token_str)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_owner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.owner:
        raise HTTPException(status_code=403, detail="Owner role required")
    return current_user


def require_guest(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.guest:
        raise HTTPException(status_code=403, detail="Guest role required")
    return current_user
