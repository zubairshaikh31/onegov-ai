"""
Generic async repository base class.
Provides standard CRUD operations so every repository avoids boilerplate.
Concrete repositories extend this and add domain-specific query methods.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Async repository providing create, read, update, soft-delete operations
    for any SQLAlchemy model that inherits BaseModel.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelType:
        """Instantiate, persist, and return a new model instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()  # flush to get the DB-generated ID without committing
        await self.db.refresh(instance)
        return instance

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, id: uuid.UUID, *, include_deleted: bool = False) -> ModelType | None:
        """Return a single record by primary key, or None if not found."""
        stmt = select(self.model).where(self.model.id == id)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """Return a paginated list of all records."""
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, include_deleted: bool = False) -> int:
        """Return total count of records."""
        stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, id: uuid.UUID, **kwargs: Any) -> ModelType | None:
        """Partially update a record by ID. Returns updated instance or None."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    # ── Delete ────────────────────────────────────────────────────────────────

    async def soft_delete(self, id: uuid.UUID) -> bool:
        """Mark a record as deleted without removing it from the database."""
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def hard_delete(self, id: uuid.UUID) -> bool:
        """Permanently remove a record. Use only where legally required."""
        instance = await self.get_by_id(id, include_deleted=True)
        if instance is None:
            return False
        await self.db.delete(instance)
        return True

    # ── Existence check ───────────────────────────────────────────────────────

    async def exists(self, **filters: Any) -> bool:
        """Return True if any active record matches the given column filters."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.deleted_at.is_(None))
        )
        for column_name, value in filters.items():
            stmt = stmt.where(getattr(self.model, column_name) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one() > 0
