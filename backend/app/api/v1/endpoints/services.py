"""
OneGov AI — Services Endpoints
Provides full listing, filtering, slug retrieval with full relational graph.
"""

from uuid import UUID
from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import DbDep, OptionalCurrentUser
from app.models.government import (
    ApplicationStep,
    Category,
    Department,
    FAQ,
    Ministry,
    RequiredDocument,
    Scheme,
    Service,
    ServiceDocument,
    ServiceRelation,
)
from app.models.activity import Bookmark, GovernmentOffice
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=ApiResponse[dict])
async def list_services(
    db: DbDep,
    q: str | None = Query(None, description="Keyword search query"),
    category_slug: str | None = Query(None, description="Category slug filter"),
    ministry_slug: str | None = Query(None, description="Ministry slug filter"),
    is_online: bool | None = Query(None, description="Filter online availability"),
    is_featured: bool | None = Query(None, description="Filter featured services"),
    sort_by: str = Query("featured", description="'featured', 'popular', 'name', 'newest'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """List services with advanced filtering, sorting, and pagination."""
    stmt = (
        select(Service)
        .where(Service.deleted_at.is_(None), Service.is_active.is_(True))
        .options(
            selectinload(Service.category),
            selectinload(Service.department).selectinload(Department.ministry),
        )
    )

    if q:
        q_like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Service.name.ilike(q_like),
                Service.short_description.ilike(q_like),
                Service.description.ilike(q_like),
                Service.slug.ilike(q_like),
            )
        )

    if category_slug:
        stmt = stmt.join(Service.category).where(Category.slug == category_slug)

    if ministry_slug:
        stmt = stmt.join(Service.department).join(Department.ministry).where(Ministry.slug == ministry_slug)

    if is_online is not None:
        stmt = stmt.where(Service.is_online == is_online)

    if is_featured is not None:
        stmt = stmt.where(Service.is_featured == is_featured)

    # Count total matching
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    # Sorting
    if sort_by == "popular":
        stmt = stmt.order_by(Service.view_count.desc(), Service.name)
    elif sort_by == "name":
        stmt = stmt.order_by(Service.name)
    elif sort_by == "newest":
        stmt = stmt.order_by(Service.created_at.desc())
    else:
        stmt = stmt.order_by(Service.is_featured.desc(), Service.view_count.desc(), Service.name)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for s in rows:
        d = s.to_dict()
        d["category"] = s.category.to_dict() if s.category else None
        d["department"] = s.department.to_dict() if s.department else None
        d["ministry"] = s.department.ministry.to_dict() if (s.department and s.department.ministry) else None
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
async def get_featured_services(db: DbDep) -> ApiResponse[list]:
    """Get curated featured services for the homepage."""
    stmt = (
        select(Service)
        .where(Service.deleted_at.is_(None), Service.is_active.is_(True))
        .options(selectinload(Service.category))
        .order_by(Service.is_featured.desc(), Service.view_count.desc())
        .limit(8)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = []
    for s in rows:
        d = s.to_dict()
        d["category"] = s.category.to_dict() if s.category else None
        items.append(d)
    return ApiResponse.ok(data=items)


@router.get("/{slug}", response_model=ApiResponse[dict])
async def get_service_detail(
    slug: str,
    db: DbDep,
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[dict]:
    """
    Retrieve full service details including category, ministry, required documents,
    step-by-step application process, FAQs, related services, and schemes.
    """
    # 1. Fetch main service with category & department
    stmt = (
        select(Service)
        .where(Service.slug == slug, Service.deleted_at.is_(None))
        .options(
            selectinload(Service.category),
            selectinload(Service.department).selectinload(Department.ministry),
        )
    )
    service = (await db.execute(stmt)).scalar_one_or_none()
    if not service:
        raise NotFoundError(f"Service '{slug}' not found.")

    # 2. Extract base data before any updates
    service_id = service.id
    data = service.to_dict()
    data["category"] = service.category.to_dict() if service.category else None
    data["department"] = service.department.to_dict() if service.department else None
    data["ministry"] = (
        service.department.ministry.to_dict()
        if (service.department and service.department.ministry)
        else None
    )

    # 3. Check bookmark
    is_bookmarked = False
    if current_user:
        bm_stmt = select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.entity_type == "service",
            Bookmark.entity_id == service_id,
        )
        bm = (await db.execute(bm_stmt)).scalar_one_or_none()
        is_bookmarked = bm is not None

    # 4. Fetch application steps directly
    steps_stmt = (
        select(ApplicationStep)
        .where(ApplicationStep.service_id == service_id)
        .order_by(ApplicationStep.step_number.asc())
    )
    step_rows = (await db.execute(steps_stmt)).scalars().all()
    steps = [
        {
            "step_number": st.step_number,
            "title": st.title,
            "description": st.description,
            "step_type": st.step_type,
            "action_url": st.action_url,
            "estimated_time": st.estimated_time,
        }
        for st in step_rows
    ]

    # 5. Fetch required documents directly
    doc_stmt = (
        select(ServiceDocument, RequiredDocument)
        .join(RequiredDocument, ServiceDocument.document_id == RequiredDocument.id)
        .where(ServiceDocument.service_id == service_id)
    )
    doc_rows = (await db.execute(doc_stmt)).all()
    documents = [
        {
            "id": str(rd.id),
            "name": rd.name,
            "description": rd.description,
            "is_mandatory": sd.is_mandatory,
            "notes": sd.notes,
            "example_url": rd.example_url,
        }
        for sd, rd in doc_rows
    ]

    # 6. Fetch FAQs directly
    faq_stmt = (
        select(FAQ)
        .where(FAQ.entity_type == "service", FAQ.entity_id == service_id)
        .order_by(FAQ.display_order.asc())
    )
    faq_rows = (await db.execute(faq_stmt)).scalars().all()
    faqs = [
        {
            "id": str(f.id),
            "question": f.question,
            "answer": f.answer,
        }
        for f in faq_rows
    ]

    # 7. Fetch related services
    rel_stmt = (
        select(ServiceRelation)
        .where(ServiceRelation.service_id == service_id)
    )
    relations = (await db.execute(rel_stmt)).scalars().all()
    related_services = []
    if relations:
        rel_ids = [r.related_service_id for r in relations]
        r_svc_stmt = select(Service.name, Service.slug, Service.short_description).where(Service.id.in_(rel_ids))
        r_rows = (await db.execute(r_svc_stmt)).all()
        related_services = [{"name": r[0], "slug": r[1], "description": r[2]} for r in r_rows]

    # 8. Fetch related schemes
    sch_stmt = select(Scheme).where(Scheme.service_id == service_id).limit(4)
    schemes = (await db.execute(sch_stmt)).scalars().all()

    # Fetch linked YouTube tutorial videos
    from app.models.intelligence import Video, ServiceVideo
    video_stmt = (
        select(Video)
        .join(ServiceVideo, Video.id == ServiceVideo.video_id)
        .where(ServiceVideo.service_id == service_id)
        .order_by(ServiceVideo.display_order.asc())
    )
    video_rows = (await db.execute(video_stmt)).scalars().all()
    videos = [
        {
            "id": str(v.id),
            "youtube_video_id": v.youtube_video_id,
            "youtube_url": v.youtube_url,
            "title": v.title,
            "channel_name": v.channel_name,
            "description": v.description,
            "thumbnail_url": v.thumbnail_url,
        }
        for v in video_rows
    ]

    # 9. Asynchronously update view count with synchronize_session=False
    try:
        await db.execute(
            update(Service)
            .where(Service.id == service_id)
            .values(view_count=Service.view_count + 1)
            .execution_options(synchronize_session=False)
        )
    except Exception:
        pass

    data["documents"] = documents
    data["application_steps"] = steps
    data["faqs"] = faqs
    data["related_services"] = related_services
    data["related_schemes"] = [sc.to_dict() for sc in schemes]
    data["is_bookmarked"] = is_bookmarked
    data["videos"] = videos

    return ApiResponse.ok(data=data)
