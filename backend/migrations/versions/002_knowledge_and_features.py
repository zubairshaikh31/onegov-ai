"""Knowledge chunks, contact messages, and extended service metadata.

Revision ID: 002_knowledge_and_features
Revises: 001_initial_schema
Create Date: 2025-02-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "002_knowledge_and_features"
down_revision: Union[str, None] = "001_initial_schema"
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


def upgrade() -> None:
    # ── Add extra columns to services if not present ──────────────────────────
    op.add_column("services", sa.Column("sub_category", sa.String(150), nullable=True))
    op.add_column("services", sa.Column("government_level", sa.String(50), nullable=True, server_default="'Central'"))
    op.add_column("services", sa.Column("state_id", sa.String(50), nullable=True))
    op.add_column("services", sa.Column("benefits", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("official_apply_link", sa.String(500), nullable=True))
    op.add_column("services", sa.Column("helpline_number", sa.String(100), nullable=True))
    op.add_column("services", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("services", sa.Column("validity", sa.String(100), nullable=True))
    op.add_column("services", sa.Column("languages_available", postgresql.JSONB(), nullable=True))
    op.add_column("services", sa.Column("source_url", sa.String(500), nullable=True))
    op.add_column("services", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("ai_explanation", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("common_questions", postgresql.JSONB(), nullable=True))
    op.add_column("services", sa.Column("common_mistakes", postgresql.JSONB(), nullable=True))
    op.add_column("services", sa.Column("search_keywords", postgresql.JSONB(), nullable=True))
    op.add_column("services", sa.Column("suggested_followups", postgresql.JSONB(), nullable=True))
    op.add_column("services", sa.Column("download_forms", postgresql.JSONB(), nullable=True))

    # ── Add extra columns to schemes if not present ───────────────────────────
    op.add_column("schemes", sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True))
    op.add_column("schemes", sa.Column("government_level", sa.String(50), nullable=True, server_default="'Central'"))
    op.add_column("schemes", sa.Column("official_portal", sa.String(500), nullable=True))

    # ── Knowledge Chunks (RAG Vector Store) ───────────────────────────────────
    from app.core.config import settings
    embedding_type = Vector(768) if settings.USE_PGVECTOR else postgresql.ARRAY(sa.Float)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_slug", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", embedding_type, nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_knowledge_chunks_type", "knowledge_chunks", ["entity_type"])
    op.create_index("ix_knowledge_chunks_entity_id", "knowledge_chunks", ["entity_id"])
    op.create_index("ix_knowledge_chunks_slug", "knowledge_chunks", ["entity_slug"])
    op.create_index("ix_knowledge_chunks_title", "knowledge_chunks", ["title"])
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_fts ON knowledge_chunks
        USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(chunk_text,'')))
    """)

    # ── Contact Messages ──────────────────────────────────────────────────────
    op.create_table(
        "contact_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'new'"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_contact_messages_email", "contact_messages", ["email"])
    op.create_index("ix_contact_messages_status", "contact_messages", ["status"])


def downgrade() -> None:
    op.drop_table("contact_messages")
    op.drop_table("knowledge_chunks")
    op.drop_column("schemes", "official_portal")
    op.drop_column("schemes", "government_level")
    op.drop_column("schemes", "service_id")
    for col in [
        "download_forms", "suggested_followups", "search_keywords", "common_mistakes",
        "common_questions", "ai_explanation", "ai_summary", "source_url", "languages_available",
        "validity", "email", "helpline_number", "official_apply_link", "benefits",
        "state_id", "government_level", "sub_category"
    ]:
        op.drop_column("services", col)
