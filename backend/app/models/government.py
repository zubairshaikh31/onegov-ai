"""
Government content models: Ministries, Departments, Categories, Services, Schemes, Knowledge Chunks.
These are the core entities that citizens search and interact with.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
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
from sqlalchemy.types import UserDefinedType

class SafeVector(UserDefinedType):
    """
    A custom SQLAlchemy type that compiles to pgvector's VECTOR
    if pgvector is enabled, otherwise falls back to FLOAT[] (double precision array).
    """
    cache_ok = True

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self, **kw):
        from app.core.config import settings
        if getattr(settings, "USE_PGVECTOR", True):
            return f"VECTOR({self.dim})"
        return "FLOAT[]"

    def bind_processor(self, dialect):
        from app.core.config import settings
        use_pgvector = getattr(settings, "USE_PGVECTOR", True)
        def process(value):
            if value is None:
                return None
            if use_pgvector:
                return "[" + ",".join(map(str, value)) + "]"
            return list(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                return [float(x) for x in value.strip("[]").split(",")]
            return list(value)
        return process

    class comparator_factory(UserDefinedType.Comparator):
        def cosine_distance(self, other):
            from app.core.config import settings
            if getattr(settings, "USE_PGVECTOR", True):
                return self.op('<=>', return_type=Float)(other)
            return self.op('==', return_type=Boolean)(other)

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


# ── Ministry ──────────────────────────────────────────────────────────────────

class Ministry(BaseModel):
    """Central or State Ministry."""

    __tablename__ = "ministries"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ministry_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="central",
        comment="'central' or 'state'"
    )
    state_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Populated only for state ministries"
    )
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    departments: Mapped[list["Department"]] = relationship(
        "Department", back_populates="ministry"
    )

    def __repr__(self) -> str:
        return f"<Ministry {self.short_name or self.name}>"


# ── Department ────────────────────────────────────────────────────────────────

class Department(BaseModel):
    """Government department under a ministry."""

    __tablename__ = "departments"

    ministry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ministries.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    ministry: Mapped[Ministry] = relationship(Ministry, back_populates="departments")
    services: Mapped[list["Service"]] = relationship("Service", back_populates="department")
    offices: Mapped[list["GovernmentOffice"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "GovernmentOffice", back_populates="department"
    )

    def __repr__(self) -> str:
        return f"<Department {self.name}>"


# ── Category ──────────────────────────────────────────────────────────────────

class Category(BaseModel):
    """
    Service category tree.
    Supports one level of parent-child nesting (top-level and sub-category).
    """

    __tablename__ = "categories"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Lucide icon name"
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    services: Mapped[list["Service"]] = relationship("Service", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


# ── Service ───────────────────────────────────────────────────────────────────

class Service(BaseModel):
    """
    A government service that citizens can apply for.
    e.g. Passport Application, Driving Licence, PAN Card, Aadhaar Update
    """

    __tablename__ = "services"

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(150), nullable=True)
    government_level: Mapped[str | None] = mapped_column(String(50), nullable=True, default="Central")
    state_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    eligibility_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    fee_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fee_amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Fee in INR paise (1 rupee = 100 paise)"
    )
    processing_time: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="e.g. '15 working days'"
    )
    validity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    official_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    official_apply_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    helpline_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_online: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Can be applied for online"
    )
    is_offline: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Can be applied for in person"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True, comment="Search tags: ['passport', 'travel', 'id']"
    )
    languages_available: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_questions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    common_mistakes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    search_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    suggested_followups: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    download_forms: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)

    # ── Multilingual content ──────────────────────────────────────────────
    name_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_hi: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Operation mode & status ───────────────────────────────────────────
    service_mode: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="ONLINE, OFFLINE, HYBRID"
    )
    service_status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", nullable=False,
        comment="ACTIVE, INACTIVE, TEMPORARILY_UNAVAILABLE, ARCHIVED"
    )
    processing_days_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_days_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Provenance / verification ─────────────────────────────────────────
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="OFFICIAL_GOVERNMENT, OFFICIAL_PORTAL, OFFICIAL_MINISTRY, ..."
    )
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="UNVERIFIED", nullable=False, index=True,
        comment="VERIFIED, PARTIALLY_VERIFIED, STALE, CONFLICTING, UNVERIFIED, ARCHIVED"
    )
    verification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    crawl_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    official_source: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_language: Mapped[str | None] = mapped_column(String(20), nullable=True, default="en")

    category: Mapped[Category | None] = relationship(Category, back_populates="services")
    department: Mapped[Department | None] = relationship(
        Department, back_populates="services"
    )
    documents: Mapped[list["ServiceDocument"]] = relationship(
        "ServiceDocument", back_populates="service", cascade="all, delete-orphan"
    )
    application_steps: Mapped[list["ApplicationStep"]] = relationship(
        "ApplicationStep", back_populates="service",
        order_by="ApplicationStep.step_number",
        cascade="all, delete-orphan",
    )
    faqs: Mapped[list["FAQ"]] = relationship(
        "FAQ",
        primaryjoin="and_(FAQ.entity_type=='service', FAQ.entity_id==Service.id)",
        foreign_keys="[FAQ.entity_id]",
        cascade="all, delete-orphan",
        overlaps="faqs",
    )
    keywords: Mapped[list["Keyword"]] = relationship(
        "Keyword",
        primaryjoin="and_(Keyword.entity_type=='service', Keyword.entity_id==Service.id)",
        foreign_keys="[Keyword.entity_id]",
        cascade="all, delete-orphan",
        overlaps="keywords",
    )

    def __repr__(self) -> str:
        return f"<Service {self.name}>"


# ── Service Documents ─────────────────────────────────────────────────────────

class RequiredDocument(BaseModel):
    """Master list of document types (e.g. Aadhaar Card, PAN Card, Photo)."""

    __tablename__ = "required_documents"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    service_links: Mapped[list["ServiceDocument"]] = relationship(
        "ServiceDocument", back_populates="document"
    )


class ServiceDocument(BaseModel):
    """Many-to-many: services ↔ required_documents with extra context."""

    __tablename__ = "service_documents"
    __table_args__ = (
        UniqueConstraint("service_id", "document_id", name="uq_service_document"),
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("required_documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="e.g. 'Self-attested copy required'"
    )

    service: Mapped[Service] = relationship(Service, back_populates="documents")
    document: Mapped[RequiredDocument] = relationship(
        RequiredDocument, back_populates="service_links"
    )


# ── Application Steps ─────────────────────────────────────────────────────────

class ApplicationStep(BaseModel):
    """Ordered steps for applying for a service."""

    __tablename__ = "application_steps"

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="general",
        comment="'online', 'offline', 'general'"
    )
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_time: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="e.g. '10 minutes'"
    )

    service: Mapped[Service] = relationship(Service, back_populates="application_steps")


# ── Scheme ────────────────────────────────────────────────────────────────────

class Scheme(BaseModel):
    """
    Government welfare scheme (Central or State).
    e.g. PM Kisan, Ayushman Bharat, Ladki Bahin Yojana
    """

    __tablename__ = "schemes"

    ministry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ministries.id", ondelete="SET NULL"), nullable=True
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheme_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="central",
        comment="'central' or 'state'"
    )
    government_level: Mapped[str | None] = mapped_column(String(50), nullable=True, default="Central")
    state_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_beneficiary: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="e.g. 'Farmers', 'Women', 'Senior Citizens'"
    )
    eligibility_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_amount: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="e.g. '₹6,000 per year'"
    )
    application_deadline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    official_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    official_portal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # ── Structured scheme content ─────────────────────────────────────────
    required_documents: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    application_process: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    languages: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=["en"])
    name_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_hi: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Provenance / verification ─────────────────────────────────────────
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="UNVERIFIED", nullable=False, index=True
    )
    verification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    crawl_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    official_source: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_language: Mapped[str | None] = mapped_column(String(20), nullable=True, default="en")

    ministry: Mapped[Ministry | None] = relationship(Ministry)
    service: Mapped[Service | None] = relationship(Service)
    faqs: Mapped[list["FAQ"]] = relationship(
        "FAQ",
        primaryjoin="and_(FAQ.entity_type=='scheme', FAQ.entity_id==Scheme.id)",
        foreign_keys="[FAQ.entity_id]",
        cascade="all, delete-orphan",
        overlaps="faqs",
    )

    def __repr__(self) -> str:
        return f"<Scheme {self.name}>"


# ── FAQ ───────────────────────────────────────────────────────────────────────

class FAQ(BaseModel):
    """Frequently Asked Question linked to a service or scheme."""

    __tablename__ = "faqs"

    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="'service' or 'scheme' or 'general'"
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ── Keyword ───────────────────────────────────────────────────────────────────

class Keyword(BaseModel):
    """Search keywords for services and schemes (for better discoverability)."""

    __tablename__ = "keywords"

    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ── Service Relations ─────────────────────────────────────────────────────────

class ServiceRelation(BaseModel):
    """Related services (e.g. 'After getting a passport, you may need a visa')."""

    __tablename__ = "service_relations"
    __table_args__ = (
        UniqueConstraint("service_id", "related_service_id", name="uq_service_relation"),
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    related_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="related",
        comment="'related', 'prerequisite', 'follow_up', 'complementary', 'alternative'"
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ── Knowledge Chunks (RAG Vector Store) ───────────────────────────────────────

class KnowledgeChunk(BaseModel):
    """
    Knowledge base chunks indexed for pgvector similarity search & RAG.
    Covers services, schemes, FAQs, eligibility rules, summaries, life events, acts, rules.
    """

    __tablename__ = "knowledge_chunks"

    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="'service', 'scheme', 'faq', 'summary', 'eligibility', 'department', 'ministry', 'life_event', 'general'"
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    entity_slug: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any | None] = mapped_column(SafeVector(768), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<KnowledgeChunk {self.entity_type}:{self.title[:40]}>"
