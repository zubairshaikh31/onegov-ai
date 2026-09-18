"""
Authentication Pydantic schemas (Data Transfer Objects).
These are the shapes of JSON bodies the API accepts and returns.
"""

import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Validators ────────────────────────────────────────────────────────────────

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,64}$"
)


def _validate_password(v: str) -> str:
    if not _PASSWORD_PATTERN.match(v):
        raise ValueError(
            "Password must be 8–64 characters and include at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character (@$!%*?&)"
        )
    return v


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """POST /auth/register"""

    full_name: str = Field(
        ..., min_length=2, max_length=150, examples=["Aarav Sharma"]
    )
    email: EmailStr = Field(..., examples=["aarav@example.com"])
    password: str = Field(..., min_length=8, max_length=64)
    phone: str | None = Field(
        default=None,
        pattern=r"^\+?[1-9]\d{9,14}$",
        examples=["+919876543210"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class RegisterResponse(BaseModel):
    """Returned after successful registration (before OTP verification)."""

    user_id: UUID
    email: str
    message: str = "Registration successful. Please verify your email with the OTP sent."


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """POST /auth/login"""

    email: EmailStr = Field(..., examples=["aarav@example.com"])
    password: str = Field(..., min_length=1, max_length=128)


class TokenPair(BaseModel):
    """Access + refresh token pair returned after successful auth."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class LoginResponse(TokenPair):
    """Extended token response including basic user info."""

    user_id: UUID
    email: str
    full_name: str
    role: str
    is_admin: bool


# ── OTP ───────────────────────────────────────────────────────────────────────

class VerifyOTPRequest(BaseModel):
    """POST /auth/verify-otp"""

    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOTPRequest(BaseModel):
    """POST /auth/resend-otp"""

    email: EmailStr


# ── Token Refresh ─────────────────────────────────────────────────────────────

class RefreshTokenRequest(BaseModel):
    """POST /auth/refresh. The refresh token may come from the HttpOnly cookie
    when `refresh_token` is omitted."""

    refresh_token: str = Field("", min_length=0)


# ── Password Management ───────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """POST /auth/forgot-password"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """POST /auth/reset-password"""

    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ChangePasswordRequest(BaseModel):
    """POST /auth/change-password (authenticated)"""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ── Google OAuth ──────────────────────────────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    """POST /auth/google — frontend sends the ID token received from Google Sign-In."""

    id_token: str = Field(..., min_length=1, description="Google ID token from client")


GoogleOAuthRequest = GoogleLoginRequest


# ── Phone OTP ─────────────────────────────────────────────────────────────────

class PhoneOTPRequest(BaseModel):
    """POST /auth/phone/send-otp"""

    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", examples=["+919876543210"])


class VerifyPhoneOTPRequest(BaseModel):
    """POST /auth/phone/verify-otp"""

    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", examples=["+919876543210"])
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutRequest(BaseModel):
    """POST /auth/logout"""

    refresh_token: str = Field(..., min_length=1)
