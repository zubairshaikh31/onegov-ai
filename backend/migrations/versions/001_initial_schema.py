"""Initial database schema — Phase 1.

Creates all core tables:
  - roles, permissions, role_permissions
  - users, user_roles
  - ministries, departments, categories
  - services, required_documents, service_documents, application_steps
  - schemes, faqs, keywords, service_relations
  - bookmarks, notifications, search_history, ai_chat_history
  - feedback, government_offices, analytics, audit_logs

Revision ID: 001
Revises: —
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Shared column defaults
UUID_DEFAULT = sa.text("gen_random_uuid()")
NOW = sa.text("now()")


def _timestamps() -> list[sa.Column]:
    """Return the 3 timestamp columns added to every table."""
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    from app.core.config import settings
    if settings.USE_PGVECTOR:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # ── Roles ──────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        *_timestamps(),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # ── Permissions ────────────────────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_permissions_name", "permissions", ["name"], unique=True)

    # ── Role ↔ Permission ──────────────────────────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── Users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="'en'"),
        sa.Column("preferred_state", sa.String(100), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_users_email",     "users", ["email"],     unique=True)
    op.create_index("ix_users_phone",     "users", ["phone"],     unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # ── User ↔ Role ────────────────────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )

    # ── Ministries ─────────────────────────────────────────────────────────────
    op.create_table(
        "ministries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("ministry_type", sa.String(20), nullable=False, server_default="'central'"),
        sa.Column("state_name", sa.String(100), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_ministries_slug", "ministries", ["slug"], unique=True)

    # ── Departments ────────────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("ministry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ministries.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_departments_slug",       "departments", ["slug"],       unique=True)
    op.create_index("ix_departments_ministry_id","departments", ["ministry_id"])

    # ── Categories ─────────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    # ── Services ───────────────────────────────────────────────────────────────
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("short_description", sa.String(500), nullable=True),
        sa.Column("eligibility_description", sa.Text, nullable=True),
        sa.Column("fee_description", sa.String(500), nullable=True),
        sa.Column("fee_amount", sa.Integer, nullable=True),
        sa.Column("processing_time", sa.String(100), nullable=True),
        sa.Column("official_url", sa.String(500), nullable=True),
        sa.Column("is_online", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_offline", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bookmark_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_services_slug",       "services", ["slug"],       unique=True)
    op.create_index("ix_services_name",       "services", ["name"])
    op.create_index("ix_services_is_active",  "services", ["is_active"])
    op.create_index("ix_services_is_featured","services", ["is_featured"])
    # Full-text search index on name + description
    op.execute("""
        CREATE INDEX ix_services_fts ON services
        USING GIN (to_tsvector('english', coalesce(name,'') || ' ' || coalesce(short_description,'')))
    """)

    # ── Required Documents ─────────────────────────────────────────────────────
    op.create_table(
        "required_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("example_url", sa.String(500), nullable=True),
        *_timestamps(),
    )

    # ── Service ↔ Documents ────────────────────────────────────────────────────
    op.create_table(
        "service_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("required_documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.String(500), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("service_id", "document_id", name="uq_service_document"),
    )

    # ── Application Steps ──────────────────────────────────────────────────────
    op.create_table(
        "application_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("step_type", sa.String(20), nullable=False, server_default="'general'"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("estimated_time", sa.String(50), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_appsteps_service_id", "application_steps", ["service_id"])

    # ── Schemes ────────────────────────────────────────────────────────────────
    op.create_table(
        "schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("ministry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ministries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("short_description", sa.String(500), nullable=True),
        sa.Column("scheme_type", sa.String(20), nullable=False, server_default="'central'"),
        sa.Column("state_name", sa.String(100), nullable=True),
        sa.Column("target_beneficiary", sa.String(200), nullable=True),
        sa.Column("eligibility_description", sa.Text, nullable=True),
        sa.Column("benefits_description", sa.Text, nullable=True),
        sa.Column("benefit_amount", sa.String(200), nullable=True),
        sa.Column("application_deadline", sa.String(100), nullable=True),
        sa.Column("official_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_schemes_slug",      "schemes", ["slug"],      unique=True)
    op.create_index("ix_schemes_name",      "schemes", ["name"])
    op.create_index("ix_schemes_is_active", "schemes", ["is_active"])
    op.execute("""
        CREATE INDEX ix_schemes_fts ON schemes
        USING GIN (to_tsvector('english', coalesce(name,'') || ' ' || coalesce(short_description,'')))
    """)

    # ── FAQs ───────────────────────────────────────────────────────────────────
    op.create_table(
        "faqs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_faqs_entity", "faqs", ["entity_type", "entity_id"])

    # ── Keywords ───────────────────────────────────────────────────────────────
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword", sa.String(200), nullable=False),
        sa.Column("search_count", sa.Integer, nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_keywords_entity",  "keywords", ["entity_type", "entity_id"])
    op.create_index("ix_keywords_keyword", "keywords", ["keyword"])

    # ── Service Relations ──────────────────────────────────────────────────────
    op.create_table(
        "service_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("related_service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False, server_default="'related'"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("service_id", "related_service_id", name="uq_service_relation"),
    )

    # ── Bookmarks ──────────────────────────────────────────────────────────────
    op.create_table(
        "bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_bookmark"),
    )
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])

    # ── Notifications ──────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("notification_type", sa.String(20), nullable=False, server_default="'info'"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("related_entity_type", sa.String(20), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_url", sa.String(500), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    # ── Search History ─────────────────────────────────────────────────────────
    op.create_table(
        "search_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("result_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clicked_entity_type", sa.String(20), nullable=True),
        sa.Column("clicked_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])
    op.create_index("ix_search_history_query",   "search_history", ["query"])

    # ── AI Chat History ────────────────────────────────────────────────────────
    op.create_table(
        "ai_chat_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_chat_user_id",    "ai_chat_history", ["user_id"])
    op.create_index("ix_chat_session_id", "ai_chat_history", ["session_id"])

    # ── Feedback ───────────────────────────────────────────────────────────────
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"),
        *_timestamps(),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])

    # ── Government Offices ─────────────────────────────────────────────────────
    op.create_table(
        "government_offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("working_hours", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_timestamps(),
    )
    op.create_index("ix_offices_city",  "government_offices", ["city"])
    op.create_index("ix_offices_state", "government_offices", ["state"])

    # ── Analytics ──────────────────────────────────────────────────────────────
    op.create_table(
        "analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analytics_event_type", "analytics", ["event_type"])
    op.create_index("ix_analytics_created_at", "analytics", ["created_at"])

    # ── Audit Logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=UUID_DEFAULT),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'success'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_logs_user_id",    "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action",     "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ── Trigger: auto-update updated_at ───────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    for table in [
        "roles", "permissions", "users", "ministries", "departments",
        "categories", "services", "required_documents", "service_documents",
        "application_steps", "schemes", "faqs", "keywords", "bookmarks",
        "notifications", "search_history", "ai_chat_history", "feedback",
        "government_offices",
    ]:
        op.execute(f"""
            CREATE TRIGGER trigger_update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    tables = [
        "audit_logs", "analytics", "government_offices", "feedback",
        "ai_chat_history", "search_history", "notifications", "bookmarks",
        "service_relations", "keywords", "faqs", "schemes", "application_steps",
        "service_documents", "required_documents", "services", "categories",
        "departments", "ministries", "user_roles", "users",
        "role_permissions", "permissions", "roles",
    ]
    for table in tables:
        op.drop_table(table)
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
