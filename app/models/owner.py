"""Module B1: Owner onboarding."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

USAT_TOKEN_STAGED = "staged"
USAT_TOKEN_RELEASED = "released"


class PropertyType(str, enum.Enum):
    entire_home = "entire_home"
    private_room = "private_room"


class OwnerProfile(Base):
    __tablename__ = "owner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="owner_profile")
    properties = relationship("Property", back_populates="owner_profile")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_profile_id = Column(Integer, ForeignKey("owner_profiles.id"), nullable=False)

    name = Column(String(255), nullable=True)  # e.g. "Miami Beach Condo"
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=True)
    region_code = Column(String(20), nullable=False)  # NYC, FL, CA, TX

    owner_occupied = Column(Boolean, nullable=False)  # is_primary_residence
    property_type = Column(SQLEnum(PropertyType), nullable=True)
    property_type_label = Column(String(50), nullable=True)  # house, apartment, condo, townhouse
    bedrooms = Column(String(10), nullable=True)  # "1", "2", "3", "4", "5+"

    # Pre-generated USAT token: created at property registration, staged until owner releases to resident guest(s)
    usat_token = Column(String(64), unique=True, nullable=True, index=True)
    usat_token_state = Column(String(20), nullable=False, default=USAT_TOKEN_STAGED)
    usat_token_released_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Soft delete: when set, property is hidden from dashboard and invite list; can be reactivated
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Shield Mode: software monitoring/enforcement state. When ON: PASSIVE GUARD (if occupied) or ACTIVE ENFORCEMENT (if vacant).
    # Owner can turn OFF; auto-activated when Dead Man's Switch runs (owner can deactivate after).
    shield_mode_enabled = Column(Integer, nullable=False, default=0)

    owner_profile = relationship("OwnerProfile", back_populates="properties")
