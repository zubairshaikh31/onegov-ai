"""
OneGov AI — Categories Endpoints
Lists categories with active service counts.
"""

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import DbDep
from app.models.government import Category, Service
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse[list])
async def list_categories(db: DbDep) -> ApiResponse[list]:
    """List all categories with live service counts."""
    stmt = (
        select(Category)
        .where(Category.deleted_at.is_(None), Category.is_active.is_(True))
        .order_by(Category.display_order, Category.name)
    )
    cats = (await db.execute(stmt)).scalars().all()

    # Get service counts per category
    count_stmt = (
        select(Service.category_id, func.count(Service.id))
        .where(Service.deleted_at.is_(None), Service.is_active.is_(True))
        .group_by(Service.category_id)
    )
    count_rows = (await db.execute(count_stmt)).all()
    count_map = {row[0]: row[1] for row in count_rows}

    data = []
    for c in cats:
        cd = c.to_dict()
        cd["services_count"] = count_map.get(c.id, 0)
        data.append(cd)

    return ApiResponse.ok(data=data)


@router.get("/{slug}", response_model=ApiResponse[dict])
async def get_category(slug: str, db: DbDep) -> ApiResponse[dict]:
    """Get category by slug with its active services."""
    stmt = (
        select(Category)
        .where(Category.slug == slug, Category.deleted_at.is_(None))
        .options(selectinload(Category.services))
    )
    category = (await db.execute(stmt)).scalar_one_or_none()
    if not category:
        raise NotFoundError(f"Category '{slug}' not found.")

    data = category.to_dict()
    data["services"] = [s.to_dict() for s in category.services if s.is_active and s.deleted_at is None]
    return ApiResponse.ok(data=data)
