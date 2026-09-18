"""
OneGov AI — Schemes Endpoints
Provides welfare schemes catalog, filtering, and detailed scheme view.
"""

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import DbDep, OptionalCurrentUser
from app.models.government import FAQ, Ministry, Scheme, Service
from app.models.activity import Bookmark
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=ApiResponse[dict])
async def list_schemes(
    db: DbDep,
    q: str | None = Query(None, description="Search query"),
    scheme_type: str | None = Query(None, description="'central' or 'state'"),
    beneficiary: str | None = Query(None, description="Beneficiary category"),
    ministry_slug: str | None = Query(None, description="Ministry slug filter"),
    is_featured: bool | None = Query(None, description="Filter featured schemes"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """List welfare schemes with filtering by type, beneficiary, and ministry."""
    stmt = (
        select(Scheme)
        .where(Scheme.deleted_at.is_(None), Scheme.is_active.is_(True))
        .options(selectinload(Scheme.ministry))
    )

    if q:
        q_like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Scheme.name.ilike(q_like),
                Scheme.short_description.ilike(q_like),
                Scheme.description.ilike(q_like),
                Scheme.target_beneficiary.ilike(q_like),
            )
        )

    if scheme_type:
        stmt = stmt.where(Scheme.scheme_type == scheme_type.lower())

    if beneficiary:
        stmt = stmt.where(Scheme.target_beneficiary.ilike(f"%{beneficiary}%"))

    if ministry_slug:
        stmt = stmt.join(Scheme.ministry).where(Ministry.slug == ministry_slug)

    if is_featured is not None:
        stmt = stmt.where(Scheme.is_featured == is_featured)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size).order_by(Scheme.is_featured.desc(), Scheme.name)
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for sc in rows:
        d = sc.to_dict()
        d["ministry"] = sc.ministry.to_dict() if sc.ministry else None
        items.append(d)

    return ApiResponse.ok(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
        }
    )


@router.get("/featured", response_model=ApiResponse[list])
async def get_featured_schemes(db: DbDep) -> ApiResponse[list]:
    """Curated featured schemes for homepage."""
    stmt = (
        select(Scheme)
        .where(Scheme.deleted_at.is_(None), Scheme.is_active.is_(True))
        .options(selectinload(Scheme.ministry))
        .order_by(Scheme.is_featured.desc(), Scheme.name)
        .limit(6)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = []
    for sc in rows:
        d = sc.to_dict()
        d["ministry"] = sc.ministry.to_dict() if sc.ministry else None
        items.append(d)
    return ApiResponse.ok(data=items)


@router.get("/{slug}", response_model=ApiResponse[dict])
async def get_scheme_detail(
    slug: str,
    db: DbDep,
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[dict]:
    """Get full welfare scheme detail including eligibility, benefits, and linked service."""
    stmt = (
        select(Scheme)
        .where(Scheme.slug == slug, Scheme.deleted_at.is_(None))
        .options(
            selectinload(Scheme.ministry),
            selectinload(Scheme.service),
        )
    )
    scheme = (await db.execute(stmt)).scalar_one_or_none()
    if not scheme:
        raise NotFoundError(f"Scheme '{slug}' not found.")

    is_bookmarked = False
    if current_user:
        bm_stmt = select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.entity_type == "scheme",
            Bookmark.entity_id == scheme.id,
        )
        bm = (await db.execute(bm_stmt)).scalar_one_or_none()
        is_bookmarked = bm is not None

    faq_stmt = (
        select(FAQ)
        .where(FAQ.entity_type == "scheme", FAQ.entity_id == scheme.id)
        .order_by(FAQ.display_order.asc())
    )
    faq_rows = (await db.execute(faq_stmt)).scalars().all()
    faqs = [{"id": str(f.id), "question": f.question, "answer": f.answer} for f in faq_rows]

    data = scheme.to_dict()
    data["ministry"] = scheme.ministry.to_dict() if scheme.ministry else None
    data["service"] = scheme.service.to_dict() if scheme.service else None
    data["faqs"] = faqs
    data["is_bookmarked"] = is_bookmarked

    return ApiResponse.ok(data=data)
