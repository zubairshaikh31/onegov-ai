"""
SQLAlchemy 2.0 declarative base and shared mixins.
Every table in the database inherits from BaseModel.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base. All models inherit from this."""

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to a plain dictionary (excludes relationships)."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class UUIDPrimaryKeyMixin:
    """Provides a UUID primary key using PostgreSQL's native UUID type."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """Provides created_at, updated_at, and deleted_at (soft delete) columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Soft delete timestamp. NULL means record is active.",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Abstract base for all application models.
    Provides: UUID primary key, timestamps, soft delete.
    """

    __abstract__ = True
