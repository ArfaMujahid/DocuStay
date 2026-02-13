"""Module A: User and authentication."""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    owner = "owner"
    guest = "guest"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "role", name="uq_users_email_role"),)

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)

    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)

    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_code = Column(String(10), nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
