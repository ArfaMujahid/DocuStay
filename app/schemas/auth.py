"""Module A: Auth schemas."""
from pydantic import BaseModel, EmailStr, model_validator
from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str = ""
    password: str
    confirm_password: str = ""
    country: str = "USA"
    state: str
    city: str
    terms_agreed: bool = False
    privacy_agreed: bool = False
    role: UserRole = UserRole.owner
    poa_signature_id: int | None = None  # required when role is owner (Master POA signed at signup)

    @model_validator(mode="after")
    def passwords_match_and_agreed(self):
        if self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        if not self.terms_agreed or not self.privacy_agreed:
            raise ValueError("You must agree to Terms and Privacy Policy")
        if self.role == UserRole.owner and (self.poa_signature_id is None or self.poa_signature_id < 1):
            raise ValueError("You must sign the Master Power of Attorney before creating an owner account")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: UserRole | None = None  # Required to distinguish owner vs guest when same email has both


class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    full_name: str | None = None
    phone: str | None = None
    state: str | None = None
    city: str | None = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: int
    email: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GuestRegister(BaseModel):
    """Guest registration; invitation_code optional. With code but no agreement_signature_id, account is created and invite is added as pending."""
    invitation_id: str = ""
    invitation_code: str = ""
    full_name: str
    email: EmailStr
    phone: str = ""
    password: str
    confirm_password: str = ""
    permanent_address: str
    permanent_city: str
    permanent_state: str
    permanent_zip: str
    terms_agreed: bool = False
    privacy_agreed: bool = False
    guest_status_acknowledged: bool = False
    no_tenancy_acknowledged: bool = False
    vacate_acknowledged: bool = False
    agreement_signature_id: int | None = None  # optional; when set with valid invite, creates stay; otherwise invite is pending on dashboard

    @model_validator(mode="after")
    def passwords_match_and_agreed(self):
        if self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        if not self.terms_agreed or not self.privacy_agreed:
            raise ValueError("You must agree to Terms and Privacy Policy")
        if not self.guest_status_acknowledged or not self.no_tenancy_acknowledged or not self.vacate_acknowledged:
            raise ValueError("You must acknowledge all guest and vacate terms")
        return self


class AcceptInvite(BaseModel):
    """Accept an invitation as an existing guest (creates Stay, marks invitation accepted)."""
    invitation_code: str
    agreement_signature_id: int


class VerifyEmailRequest(BaseModel):
    """Verify email with code sent after registration."""
    user_id: int
    code: str


class ResendVerificationRequest(BaseModel):
    """Request a new verification code for pending signup."""
    user_id: int


class RegisterPendingResponse(BaseModel):
    """Response from register when email verification is required (no token yet)."""
    user_id: int
    message: str = "Check your email for the verification code."
