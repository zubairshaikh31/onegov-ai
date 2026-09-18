"""User repository — domain-specific queries for the users table."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(
        self, email: str, *, include_deleted: bool = False
    ) -> User | None:
        """Fetch a user by email address (case-insensitive)."""
        stmt = (
            select(User)
            .where(User.email == email.lower().strip())
            .options(selectinload(User.roles))
        )
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Fetch an OAuth user by their Google subject identifier."""
        stmt = (
            select(User)
            .where(User.google_id == google_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_roles(self, user_id: object) -> User | None:
        """Fetch a user and eagerly load their roles."""
        import uuid as _uuid
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            select(User)
            .where(User.id == uid, User.deleted_at.is_(None))
            .options(selectinload(User.roles))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return True if the email is already registered (active or deleted)."""
        return await self.exists(email=email.lower().strip())

    async def increment_failed_attempts(self, user_id: object) -> int:
        """
        Atomically increment failed login counter.
        Returns the new count so the caller can decide to lock the account.
        """
        import uuid as _uuid
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            update(User)
            .where(User.id == uid)
            .values(failed_login_attempts=User.failed_login_attempts + 1)
            .returning(User.failed_login_attempts)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def reset_failed_attempts(self, user_id: object) -> None:
        """Reset the failed login counter after a successful authentication."""
        import uuid as _uuid
        from datetime import datetime, timezone
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            update(User)
            .where(User.id == uid)
            .values(
                failed_login_attempts=0,
                locked_until=None,
                last_login_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)

    async def lock_account(self, user_id: object, locked_until: object) -> None:
        """Lock a user account until the given datetime."""
        import uuid as _uuid
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            update(User)
            .where(User.id == uid)
            .values(locked_until=locked_until)
        )
        await self.db.execute(stmt)

    async def mark_email_verified(self, user_id: object) -> None:
        """Mark user email as verified."""
        import uuid as _uuid
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            update(User)
            .where(User.id == uid)
            .values(is_email_verified=True)
        )
        await self.db.execute(stmt)

    async def update_password(self, user_id: object, new_hash: str) -> None:
        """Update password hash and invalidate all existing tokens via the service layer."""
        import uuid as _uuid
        uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
        stmt = (
            update(User)
            .where(User.id == uid)
            .values(password_hash=new_hash)
        )
        await self.db.execute(stmt)
