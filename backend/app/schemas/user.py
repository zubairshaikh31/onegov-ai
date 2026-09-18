"""User-facing Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RoleSchema(BaseModel):
    id: UUID
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    """Public user profile returned in most responses."""

    id: UUID
    email: str
    full_name: str
    phone: str | None
    avatar_url: str | None
    is_active: bool
    is_email_verified: bool
    preferred_language: str
    preferred_state: str | None
    roles: list[RoleSchema]
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """PATCH /users/me"""

    full_name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(None, pattern=r"^\+?[1-9]\d{9,14}$")
    avatar_url: str | None = Field(None, max_length=500)
    preferred_language: str | None = Field(None, pattern=r"^(en|hi|mr)$")
    preferred_state: str | None = Field(None, max_length=100)


class AdminUserView(UserProfile):
    """Extended user info for admin endpoints."""

    failed_login_attempts: int
    locked_until: datetime | None
    google_id: str | None

    model_config = {"from_attributes": True}
