"""
User model — the central authentication entity.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.role import Role, UserRole


class User(BaseModel):
    """
    Registered platform user.

    Auth fields:
      - password_hash: bcrypt hash, NULL for OAuth-only users
      - google_id: Google subject identifier for OAuth users
      - is_email_verified: set to True after OTP verification

    Security fields:
      - failed_login_attempts: incremented on bad password, reset on success
      - locked_until: account locked if attempts exceed MAX_FAILED_LOGIN_ATTEMPTS
      - last_login_at: updated on every successful authentication
    """

    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Auth ──────────────────────────────────────────────────────────────
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="NULL for OAuth-only (Google) users"
    )
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    # ── State ─────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Security ──────────────────────────────────────────────────────────
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Account locked until this timestamp. NULL means not locked."
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Profile extras ────────────────────────────────────────────────────
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False,
        comment="BCP 47 language tag: 'en', 'hi', 'mr'"
    )
    preferred_state: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="User's home state for state-specific scheme recommendations"
    )
    citizen_profile: Mapped[dict | None] = mapped_column(
        "citizen_profile", JSONB, nullable=True,
        comment="Optional CO-PILOT profile: age, occupation, income_range, family_status, etc. (privacy-first)",
    )
    privacy_settings: Mapped[dict | None] = mapped_column(
        "privacy_settings", JSONB, nullable=True,
        comment="analytics_enabled, ai_personalization_enabled, data_export_requested",
    )

    # ── Relationships ─────────────────────────────────────────────────────
    roles: Mapped[list[Role]] = relationship(
        Role,
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Bookmark", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    search_history: Mapped[list["SearchHistory"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "SearchHistory", back_populates="user", cascade="all, delete-orphan"
    )
    chat_history: Mapped[list["AIChatHistory"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AIChatHistory", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AuditLog", back_populates="user"
    )
    feedback: Mapped[list["Feedback"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Feedback", back_populates="user"
    )
    tasks: Mapped[list["UserTask"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "UserTask", back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["UserDocument"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "UserDocument", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Computed helpers ──────────────────────────────────────────────────
    @property
    def is_locked(self) -> bool:
        from datetime import timezone
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    @property
    def is_admin(self) -> bool:
        return "admin" in self.role_names

    def __repr__(self) -> str:
        return f"<User {self.email}>"
