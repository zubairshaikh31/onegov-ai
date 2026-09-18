"""User service — business logic for user profile management."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UpdateProfileRequest


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._users = UserRepository(db)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._users.get_by_id_with_roles(user_id)

    async def update_profile(
        self, user_id: uuid.UUID, data: UpdateProfileRequest
    ) -> User | None:
        updates = data.model_dump(exclude_none=True)
        return await self._users.update(user_id, **updates)

    async def deactivate(self, user_id: uuid.UUID) -> bool:
        result = await self._users.update(user_id, is_active=False)
        return result is not None
