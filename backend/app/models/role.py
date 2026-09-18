"""
Role and Permission models.
Implements a simple RBAC (Role-Based Access Control) system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel


# ── Association tables (pure join tables — no extra columns) ─────────────────

class RolePermission(Base):
    """Many-to-many: roles ↔ permissions."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class UserRole(Base):
    """Many-to-many: users ↔ roles."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True),
        server_default=__import__("sqlalchemy").func.now(),
    )


# ── Core models ───────────────────────────────────────────────────────────────

class Permission(BaseModel):
    """
    Fine-grained permission: (resource, action) pair.
    e.g. resource='services', action='create'
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="Unique name, e.g. 'services:create'"
    )
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Resource group, e.g. 'services', 'users', 'admin'"
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Action, e.g. 'create', 'read', 'update', 'delete'"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class Role(BaseModel):
    """
    User role.
    System roles ('admin', 'user') are protected and cannot be deleted.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="Role identifier, e.g. 'admin', 'user', 'moderator'"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="System roles cannot be deleted via the API"
    )

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        Permission,
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
