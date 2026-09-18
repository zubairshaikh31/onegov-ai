"""
OneGov AI — Ministries Endpoints
Lists central and state ministries with departments and service counts.
"""

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import DbDep
from app.models.government import Department, Ministry, Service
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/ministries", tags=["Ministries"])


@router.get("", response_model=ApiResponse[list])
async def list_ministries(db: DbDep) -> ApiResponse[list]:
    """List ministries with departments and service counts."""
    stmt = (
        select(Ministry)
        .where(Ministry.deleted_at.is_(None), Ministry.is_active.is_(True))
        .options(selectinload(Ministry.departments))
        .order_by(Ministry.name)
    )
    ministries = (await db.execute(stmt)).scalars().all()

    data = []
    for m in ministries:
        md = m.to_dict()
        md["departments_count"] = len(m.departments)
        md["departments"] = [d.to_dict() for d in m.departments if d.is_active]
        data.append(md)

    return ApiResponse.ok(data=data)


@router.get("/{slug}", response_model=ApiResponse[dict])
async def get_ministry(slug: str, db: DbDep) -> ApiResponse[dict]:
    """Get ministry detail by slug."""
    stmt = (
        select(Ministry)
        .where(Ministry.slug == slug, Ministry.deleted_at.is_(None))
        .options(selectinload(Ministry.departments).selectinload(Department.services))
    )
    ministry = (await db.execute(stmt)).scalar_one_or_none()
    if not ministry:
        raise NotFoundError(f"Ministry '{slug}' not found.")

    data = ministry.to_dict()
    data["departments"] = [
        {
            **d.to_dict(),
            "services": [s.to_dict() for s in d.services if s.is_active and s.deleted_at is None],
        }
        for d in ministry.departments
        if d.is_active and d.deleted_at is None
    ]
    return ApiResponse.ok(data=data)
