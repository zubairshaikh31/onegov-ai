"""Role repository — queries for roles and permissions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Role, db)

    async def get_by_name(self, name: str) -> Role | None:
        stmt = (
            select(Role)
            .where(Role.name == name, Role.deleted_at.is_(None))
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def assign_role_to_user(self, user: User, role: Role) -> None:
        """Add a role to a user if not already assigned."""
        if role not in user.roles:
            user.roles.append(role)
            await self.db.flush()

    async def get_all_with_permissions(self) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.deleted_at.is_(None))
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
