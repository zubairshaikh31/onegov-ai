"""
OneGov AI — Notifications Endpoints
"""

from uuid import UUID
from fastapi import APIRouter
from sqlalchemy import select, update

from app.dependencies import CurrentUser, DbDep
from app.models.activity import Notification
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse[list])
async def list_notifications(current_user: CurrentUser, db: DbDep) -> ApiResponse[list]:
    """Get in-app notifications for the user."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id, Notification.deleted_at.is_(None))
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notes = (await db.execute(stmt)).scalars().all()
    return ApiResponse.ok(data=[n.to_dict() for n in notes])


@router.post("/{notification_id}/read", response_model=ApiResponse[None])
async def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DbDep,
) -> ApiResponse[None]:
    """Mark single notification as read."""
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return ApiResponse.ok(message="Notification marked as read.")


@router.post("/read-all", response_model=ApiResponse[None])
async def mark_all_notifications_read(
    current_user: CurrentUser,
    db: DbDep,
) -> ApiResponse[None]:
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return ApiResponse.ok(message="All notifications marked as read.")
