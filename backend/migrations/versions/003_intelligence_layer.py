"""Intelligence layer: provenance, videos, source monitoring, eligibility,
citizen journeys, life events, user tasks/documents.

Revision ID: 003_intelligence_layer
Revises: 002_knowledge_and_features
Create Date: 2026-08-28 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_intelligence_layer"
down_revision: Union[str, None] = "002_knowledge_and_features"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _provenance_columns() -> list[sa.Column]:
    return [
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_title", sa.String(500), nullable=True),
        sa.Column("source_last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("verification_score", sa.Float(), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("crawl_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_version", sa.String(30), nullable=True),
        sa.Column("official_source", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_language", sa.String(20), nullable=True, server_default="en"),
    ]


def upgrade() -> None:
    # ── Services: multilingual + operations + provenance ──────────────────────
    op.add_column("services", sa.Column("name_hi", sa.String(255), nullable=True))
    op.add_column("services", sa.Column("description_hi", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("service_mode", sa.String(20), nullable=True))
    op.add_column("services", sa.Column("service_status", sa.String(30), nullable=False, server_default="ACTIVE"))
    op.add_column("services", sa.Column("processing_days_min", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("processing_days_max", sa.Integer(), nullable=True))
    for col in _provenance_columns():
        op.add_column("services", col)
    op.create_index("ix_services_verification_status", "services", ["verification_status"])
    op.create_index("ix_services_service_status", "services", ["service_status"])

    # ── Schemes: structured content + provenance ──────────────────────────────
    op.add_column("schemes", sa.Column("required_documents", postgresql.JSONB(), nullable=True))
    op.add_column("schemes", sa.Column("application_process", postgresql.JSONB(), nullable=True))
    op.add_column("schemes", sa.Column("exclusions", sa.Text(), nullable=True))
    op.add_column("schemes", sa.Column("keywords", postgresql.JSONB(), nullable=True))
    op.add_column("schemes", sa.Column("languages", postgresql.JSONB(), nullable=True, server_default=sa.text("'[\"en\"]'")))
    op.add_column("schemes", sa.Column("name_hi", sa.String(255), nullable=True))
    op.add_column("schemes", sa.Column("description_hi", sa.Text(), nullable=True))
    for col in _provenance_columns():
        op.add_column("schemes", col)
    op.create_index("ix_schemes_verification_status", "schemes", ["verification_status"])

    # ── Users: privacy & personalization ───────────────────────────────────────
    op.add_column("users", sa.Column("citizen_profile", postgresql.JSONB(), nullable=True))
    op.add_column("users", sa.Column("privacy_settings", postgresql.JSONB(), nullable=True))

    # ── Knowledge chunks: embedding provenance ────────────────────────────────
    op.add_column("knowledge_chunks", sa.Column("embedding_model", sa.String(100), nullable=True))
    op.add_column("knowledge_chunks", sa.Column("embedding_version", sa.String(30), nullable=True))
    op.add_column("knowledge_chunks", sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True))

    # ── Videos ─────────────────────────────────────────────────────────────────
    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("youtube_video_id", sa.String(64), nullable=False),
        sa.Column("youtube_url", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel_id", sa.String(100), nullable=True),
        sa.Column("channel_name", sa.String(255), nullable=True),
        sa.Column("channel_url", sa.String(500), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(20), nullable=True, server_default="en"),
        sa.Column("official_channel", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)
    op.create_index("ix_videos_title", "videos", ["title"])
    op.create_index("ix_videos_channel_name", "videos", ["channel_name"])
    op.create_index("ix_videos_verification_status", "videos", ["verification_status"])

    op.create_table(
        "service_videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(30), nullable=False, server_default="EDUCATIONAL"),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("service_id", "video_id", name="uq_service_video"),
    )
    op.create_index("ix_service_videos_service_id", "service_videos", ["service_id"])

    # ── Source monitoring ──────────────────────────────────────────────────────
    op.create_table(
        "source_monitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="OFFICIAL_GOVERNMENT"),
        sa.Column("entity_type", sa.String(30), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="DISCOVERED"),
        sa.Column("robots_ok", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_content_hash", sa.String(64), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_fetch_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_source_monitors_url", "source_monitors", ["url"])
    op.create_index("ix_source_monitors_domain", "source_monitors", ["domain"])
    op.create_index("ix_source_monitors_status", "source_monitors", ["status"])

    # ── Source change log (Service Radar / Change Tracker) ────────────────────
    op.create_table(
        "source_change_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_slug", sa.String(255), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("previous_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("new_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("diff_summary", postgresql.JSONB(), nullable=True),
        sa.Column("change_type", sa.String(30), nullable=False, server_default="UPDATE"),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="UNVERIFIED"),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_source_change_logs_entity", "source_change_logs", ["entity_type", "entity_id"])

    # ── Eligibility rules ──────────────────────────────────────────────────────
    op.create_table(
        "eligibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(20), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.String(500), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        *_timestamps(),
    )
    op.create_index("ix_eligibility_rules_entity", "eligibility_rules", ["entity_type", "entity_id"])

    # ── Citizen journeys ───────────────────────────────────────────────────────
    op.create_table(
        "citizen_journeys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
        sa.UniqueConstraint("slug", name="uq_citizen_journeys_slug"),
    )
    op.create_index("ix_citizen_journeys_slug", "citizen_journeys", ["slug"], unique=True)

    op.create_table(
        "journey_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("citizen_journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_slug", sa.String(255), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("duration_estimate", sa.String(100), nullable=True),
        sa.Column("is_optional", sa.Boolean(), nullable=False, server_default="false"),
        *_timestamps(),
        sa.UniqueConstraint("journey_id", "step_number", name="uq_journey_step_order"),
    )
    op.create_index("ix_journey_steps_journey_id", "journey_steps", ["journey_id"])
    op.create_index("ix_journey_steps_target_slug", "journey_steps", ["target_slug"])

    # ── Life events ────────────────────────────────────────────────────────────
    op.create_table(
        "life_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("service_slugs", postgresql.JSONB(), nullable=True),
        sa.Column("scheme_slugs", postgresql.JSONB(), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
        sa.UniqueConstraint("slug", name="uq_life_events_slug"),
    )
    op.create_index("ix_life_events_slug", "life_events", ["slug"], unique=True)

    # ── User task board ────────────────────────────────────────────────────────
    op.create_table(
        "user_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_slug", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("priority", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("estimated_effort", sa.String(100), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("external_url", sa.String(500), nullable=True),
        sa.Column("dependencies", postgresql.JSONB(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_user_tasks_user_id", "user_tasks", ["user_id"])

    # ── User documents (Document Intelligence) ─────────────────────────────────
    op.create_table(
        "user_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_name", sa.String(200), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("extraction", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="TEMP"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_user_documents_user_id", "user_documents", ["user_id"])

    # ── Scheme relations ───────────────────────────────────────────────────────
    op.create_table(
        "scheme_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("related_scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False, server_default="related"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("scheme_id", "related_scheme_id", name="uq_scheme_relation"),
    )


def downgrade() -> None:
    op.drop_table("scheme_relations")
    op.drop_table("user_documents")
    op.drop_table("user_tasks")
    op.drop_table("life_events")
    op.drop_table("journey_steps")
    op.drop_table("citizen_journeys")
    op.drop_table("eligibility_rules")
    op.drop_table("source_change_logs")
    op.drop_table("source_monitors")
    op.drop_table("service_videos")
    op.drop_table("videos")

    op.drop_column("knowledge_chunks", "embedded_at")
    op.drop_column("knowledge_chunks", "embedding_version")
    op.drop_column("knowledge_chunks", "embedding_model")

    op.drop_column("users", "privacy_settings")
    op.drop_column("users", "citizen_profile")

    for col in ["source_language", "official_source", "data_version", "crawl_timestamp",
                "content_hash", "verification_notes", "verification_score",
                "verification_status", "source_updated_at", "source_published_at",
                "source_last_checked", "source_title", "source_type", "source_domain",
                "processing_days_max", "processing_days_min", "service_status",
                "service_mode", "description_hi", "name_hi"]:
        op.drop_column("schemes", col)

    for col in ["source_language", "official_source", "data_version", "crawl_timestamp",
                "content_hash", "verification_notes", "verification_score",
                "verification_status", "source_updated_at", "source_published_at",
                "source_last_checked", "source_title", "source_type", "source_domain",
                "processing_days_max", "processing_days_min", "service_status",
                "service_mode", "description_hi", "name_hi"]:
        op.drop_column("services", col)