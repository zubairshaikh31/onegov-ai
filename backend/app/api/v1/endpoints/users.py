"""User profile endpoints (authenticated)."""

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser, DbDep
from app.repositories.user_repository import UserRepository
from app.schemas.common import ApiResponse
from app.schemas.user import AdminUserView, UpdateProfileRequest, UserProfile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=ApiResponse[UserProfile],
    summary="Get my profile",
)
async def get_my_profile(current_user: CurrentUser) -> ApiResponse[UserProfile]:
    profile = UserProfile.model_validate(current_user)
    return ApiResponse.ok(data=profile)


@router.patch(
    "/me",
    response_model=ApiResponse[UserProfile],
    summary="Update my profile",
)
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DbDep,
) -> ApiResponse[UserProfile]:
    repo = UserRepository(db)
    updates = body.model_dump(exclude_none=True)
    updated = await repo.update(current_user.id, **updates)
    profile = UserProfile.model_validate(updated)
    return ApiResponse.ok(data=profile, message="Profile updated.")


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ApiResponse[list[AdminUserView]],
    summary="List all users (admin)",
)
async def list_users(
    current_admin: CurrentAdmin,
    db: DbDep,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[list[AdminUserView]]:
    repo = UserRepository(db)
    offset = (page - 1) * page_size
    users = await repo.get_all(offset=offset, limit=page_size)
    return ApiResponse.ok(
        data=[AdminUserView.model_validate(u) for u in users]
    )
