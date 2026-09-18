"""
OneGov AI — Bookmarks Endpoints
"""

from uuid import UUID
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, delete

from app.dependencies import CurrentUser, DbDep
from app.models.activity import Bookmark
from app.models.government import Scheme, Service
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


class BookmarkToggleRequest(BaseModel):
    entity_type: str  # 'service' or 'scheme'
    entity_id: UUID


@router.get("", response_model=ApiResponse[dict])
async def list_bookmarks(current_user: CurrentUser, db: DbDep) -> ApiResponse[dict]:
    """Get all saved bookmarks for the authenticated user."""
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id, Bookmark.deleted_at.is_(None))
        .order_by(Bookmark.created_at.desc())
    )
    bookmarks = (await db.execute(stmt)).scalars().all()

    services_list = []
    schemes_list = []

    svc_ids = [b.entity_id for b in bookmarks if b.entity_type == "service"]
    sch_ids = [b.entity_id for b in bookmarks if b.entity_type == "scheme"]

    if svc_ids:
        s_rows = (await db.execute(select(Service).where(Service.id.in_(svc_ids)))).scalars().all()
        services_list = [s.to_dict() for s in s_rows]

    if sch_ids:
        sc_rows = (await db.execute(select(Scheme).where(Scheme.id.in_(sch_ids)))).scalars().all()
        schemes_list = [sc.to_dict() for sc in sc_rows]

    return ApiResponse.ok(
        data={
            "services": services_list,
            "schemes": schemes_list,
            "total": len(bookmarks),
        }
    )


@router.post("/toggle", response_model=ApiResponse[dict])
async def toggle_bookmark(
    body: BookmarkToggleRequest,
    current_user: CurrentUser,
    db: DbDep,
) -> ApiResponse[dict]:
    """Toggle a bookmark (add if absent, remove if present)."""
    stmt = select(Bookmark).where(
        Bookmark.user_id == current_user.id,
        Bookmark.entity_type == body.entity_type,
        Bookmark.entity_id == body.entity_id,
    )
    bm = (await db.execute(stmt)).scalar_one_or_none()

    if bm:
        await db.delete(bm)
        await db.commit()
        return ApiResponse.ok(
            data={"bookmarked": False, "entity_type": body.entity_type, "entity_id": str(body.entity_id)},
            message="Bookmark removed.",
        )
    else:
        new_bm = Bookmark(
            user_id=current_user.id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
        )
        db.add(new_bm)
        await db.commit()
        return ApiResponse.ok(
            data={"bookmarked": True, "entity_type": body.entity_type, "entity_id": str(body.entity_id)},
            message="Bookmark saved.",
        )
