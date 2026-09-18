"""
OneGov AI — Intelligence layer models.

Provenance / verification, YouTube videos, source monitoring, change tracking,
deterministic eligibility rules, citizen journeys, life events, user tasks,
user documents (document intelligence), and scheme-to-scheme relations.

All records retain full provenance so every fact shown to a citizen can be
traced back to an official source.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


# ── Verification / provenance constants ───────────────────────────────────────

class VerificationStatus:
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"
    ARCHIVED = "ARCHIVED"


class SourceType:
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    OFFICIAL_PORTAL = "OFFICIAL_PORTAL"
    OFFICIAL_MINISTRY = "OFFICIAL_MINISTRY"
    OFFICIAL_STATE_PORTAL = "OFFICIAL_STATE_PORTAL"
    OFFICIAL_DEPARTMENT = "OFFICIAL_DEPARTMENT"
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    OFFICIAL_YOUTUBE = "OFFICIAL_YOUTUBE"
    SECONDARY = "SECONDARY"
    UNVERIFIED = "UNVERIFIED"


class ServiceMode:
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    HYBRID = "HYBRID"


class ServiceStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    ARCHIVED = "ARCHIVED"


# ── YouTube Video ─────────────────────────────────────────────────────────────

class Video(BaseModel):
    """A verified educational / tutorial video linked to government services."""

    __tablename__ = "videos"

    youtube_video_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    channel_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True, default="en")
    official_channel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(30), default=VerificationStatus.UNVERIFIED, nullable=False, index=True
    )
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    service_links: Mapped[list["ServiceVideo"]] = relationship(
        "ServiceVideo", back_populates="video", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Video {self.title[:40]}>"


class ServiceVideo(BaseModel):
    """Many-to-many: services ↔ videos with relationship metadata."""

    __tablename__ = "service_videos"
    __table_args__ = (
        UniqueConstraint("service_id", "video_id", name="uq_service_video"),
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="EDUCATIONAL",
        comment="OFFICIAL_TUTORIAL, OFFICIAL_EXPLAINER, APPLICATION_GUIDE, DOCUMENT_GUIDE, EDUCATIONAL, RELATED",
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    video: Mapped[Video] = relationship(Video, back_populates="service_links")


# ── Source Monitoring ─────────────────────────────────────────────────────────

class SourceMonitor(BaseModel):
    """Crawl / monitoring state for an official source URL."""

    __tablename__ = "source_monitors"

    url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(
        String(50), default=SourceType.OFFICIAL_GOVERNMENT, nullable=False
    )
    entity_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="DISCOVERED", nullable=False, index=True,
        comment="DISCOVERED, FETCHING, OK, FAILED, CHANGED, UNCHANGED, SKIPPED",
    )
    robots_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_fetch_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Source Change Log (Service Radar / Change Tracker) ────────────────────────

class SourceChangeLog(BaseModel):
    """Detected changes on an official source, enabling the Service Radar."""

    __tablename__ = "source_change_logs"

    entity_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    entity_slug: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    previous_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    diff_summary: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, nullable=True,
        comment="e.g. [{'field': 'processing_time', 'before': '7 days', 'after': '15 days'}]",
    )
    change_type: Mapped[str] = mapped_column(
        String(30), default="UPDATE", nullable=False,
        comment="NEW, UPDATE, REMOVED, STATUS_CHANGE",
    )
    verification_status: Mapped[str] = mapped_column(
        String(30), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Deterministic Eligibility Rules ───────────────────────────────────────────

class EligibilityRule(BaseModel):
    """Structured, deterministic eligibility rules for services and schemes."""

    __tablename__ = "eligibility_rules"

    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True, comment="'service' or 'scheme'"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    field: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="age, annual_income, state, gender, category, occupation, citizenship, residency, student, farmer",
    )
    operator: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="gte, lte, eq, neq, in, not_in, contains, between",
    )
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


# ── Citizen Journey ───────────────────────────────────────────────────────────

class CitizenJourney(BaseModel):
    """A grouped set of government tasks (signature feature)."""

    __tablename__ = "citizen_journeys"

    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    steps: Mapped[list["JourneyStep"]] = relationship(
        "JourneyStep", back_populates="journey", order_by="JourneyStep.step_number",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CitizenJourney {self.name}>"


class JourneyStep(BaseModel):
    """A single step inside a citizen journey."""

    __tablename__ = "journey_steps"
    __table_args__ = (
        UniqueConstraint("journey_id", "step_number", name="uq_journey_step_order"),
    )

    journey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizen_journeys.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="'service' or 'scheme'"
    )
    target_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    duration_estimate: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    journey: Mapped[CitizenJourney] = relationship(CitizenJourney, back_populates="steps")


# ── Life Event ────────────────────────────────────────────────────────────────

class LifeEvent(BaseModel):
    """A life event that triggers a set of government services & schemes."""

    __tablename__ = "life_events"

    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    service_slugs: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    scheme_slugs: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<LifeEvent {self.name}>"


# ── User Task Board ───────────────────────────────────────────────────────────

class UserTask(BaseModel):
    """A task on the citizen's 'My Government Task Board'."""

    __tablename__ = "user_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="'service' or 'scheme'"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False,
        comment="PENDING, IN_PROGRESS, COMPLETED, BLOCKED",
    )
    priority: Mapped[str] = mapped_column(
        String(10), default="MEDIUM", nullable=False,
        comment="HIGH, MEDIUM, LOW",
    )
    estimated_effort: Mapped[str | None] = mapped_column(String(100), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dependencies: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="tasks")  # type: ignore[name-defined]  # noqa: F821


# ── User Documents (Document Intelligence) ────────────────────────────────────

class UserDocument(BaseModel):
    """A document uploaded by a citizen for document intelligence / readiness."""

    __tablename__ = "user_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )
    document_name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extraction: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True,
        comment="OCR/AI extracted fields: name, dob, identifier, expiry, etc.",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="TEMP", nullable=False,
        comment="TEMP, PROCESSED, DELETED",
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="documents")  # type: ignore[name-defined]  # noqa: F821


# ── Scheme ↔ Scheme relations ─────────────────────────────────────────────────

class SchemeRelation(BaseModel):
    """Related schemes."""

    __tablename__ = "scheme_relations"
    __table_args__ = (
        UniqueConstraint("scheme_id", "related_scheme_id", name="uq_scheme_relation"),
    )

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )
    related_scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="related",
        comment="'related', 'prerequisite', 'follow_up', 'complementary', 'alternative'"
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)