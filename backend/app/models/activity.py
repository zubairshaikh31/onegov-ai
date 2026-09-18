"""
User activity models: bookmarks, notifications, search history,
AI chat history, feedback, government offices, analytics, audit logs, and contact messages.
"""

import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TimestampMixin, UUIDPrimaryKeyMixin


# ── Bookmark ──────────────────────────────────────────────────────────────────

class Bookmark(BaseModel):
    """User-saved service or scheme."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_bookmark"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'service' or 'scheme'"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="bookmarks")  # type: ignore[name-defined]  # noqa: F821


# ── Notification ──────────────────────────────────────────────────────────────

class Notification(BaseModel):
    """In-app notification for a user."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info",
        comment="'info', 'success', 'warning', 'error'"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")  # type: ignore[name-defined]  # noqa: F821


# ── Search History ────────────────────────────────────────────────────────────

class SearchHistory(BaseModel):
    """Records every search query for personalization and analytics."""

    __tablename__ = "search_history"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicked_entity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    clicked_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="search_history")  # type: ignore[name-defined]  # noqa: F821


# ── AI Chat History ───────────────────────────────────────────────────────────

class AIChatHistory(BaseModel):
    """Individual message in an AI conversation session."""

    __tablename__ = "ai_chat_history"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Groups messages belonging to the same conversation"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="'user' or 'assistant' or 'system'"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User | None"] = relationship("User", back_populates="chat_history")  # type: ignore[name-defined]  # noqa: F821


# ── Feedback ──────────────────────────────────────────────────────────────────

class Feedback(BaseModel):
    """User rating and comment on a service or scheme."""

    __tablename__ = "feedback"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="'service', 'scheme', or 'platform'"
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1–5 star rating"
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="feedback")  # type: ignore[name-defined]  # noqa: F821


# ── Contact Message ───────────────────────────────────────────────────────────

class ContactMessage(BaseModel):
    """Submissions from the public contact form."""

    __tablename__ = "contact_messages"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)


# ── Government Office ─────────────────────────────────────────────────────────

class GovernmentOffice(BaseModel):
    """Physical government office location."""

    __tablename__ = "government_offices"

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    working_hours: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
        comment='{"monday": "9:00-17:00", "tuesday": "9:00-17:00", ...}'
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Department", back_populates="offices"
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

class Analytics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Platform analytics event.
    Write-heavy — intentionally has no updated_at or deleted_at.
    """

    __tablename__ = "analytics"

    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="e.g. 'page_view', 'service_view', 'search', 'chat_message'"
    )
    entity_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Immutable audit trail for security-sensitive actions.
    Never update or delete rows from this table.
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="e.g. 'auth.login', 'auth.login_failed', 'auth.logout', 'user.update'"
    )
    resource: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success",
        comment="'success' or 'failure'"
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")  # type: ignore[name-defined]  # noqa: F821
