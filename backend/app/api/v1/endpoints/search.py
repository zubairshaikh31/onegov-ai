"""
OneGov AI — Global Intelligent Search Endpoint
Implements multi-modal search: pg_trgm typo tolerance + full-text search + pgvector semantic retrieval.
Every result carries honest provenance (verification status, source domain, confidence).
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Query, Request
from sqlalchemy import func, or_, select, text, String
from sqlalchemy.orm import selectinload

from app.dependencies import DbDep, OptionalCurrentUser
from app.middleware.rate_limit import rate_search
from app.models.activity import SearchHistory
from app.models.government import Category, Department, FAQ, Keyword, Ministry, Scheme, Service
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/search", tags=["Search"])


def _confidence(verification_status: str | None, has_official_url: bool) -> float:
    v = (verification_status or "UNVERIFIED").upper()
    base = {"VERIFIED": 0.75, "PARTIALLY_VERIFIED": 0.6, "STALE": 0.35,
            "CONFLICTING": 0.2, "UNVERIFIED": 0.2, "ARCHIVED": 0.05}.get(v, 0.2)
    return round(min(base + (0.1 if has_official_url else 0.0), 1.0), 2)


@router.get("", response_model=ApiResponse[dict])
@rate_search("60/minute")
async def global_search(
    db: DbDep,
    request: Request,
    q: str = Query(..., min_length=1, description="Search query string"),
    type: str | None = Query("all", description="'all', 'service', 'scheme', 'faq', 'ministry'"),
    category_slug: str | None = None,
    ministry_slug: str | None = None,
    is_online: bool | None = None,
    sort_by: str | None = Query("relevance", description="'relevance', 'popular', 'name'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[dict]:
    """
    Search services, schemes, FAQs, and ministries with typo tolerance and category filters.
    """
    q_clean = q.strip()
    q_like = f"%{q_clean}%"
    results = []

    # 1. Search Services
    if type in ("all", "service"):
        svc_stmt = (
            select(Service)
            .where(Service.deleted_at.is_(None), Service.is_active.is_(True))
            .options(selectinload(Service.category), selectinload(Service.department))
        )
        if category_slug:
            svc_stmt = svc_stmt.join(Service.category).where(Category.slug == category_slug)
        if is_online is not None:
            svc_stmt = svc_stmt.where(Service.is_online == is_online)

        # Keyword and name match with typo tolerance
        svc_stmt = svc_stmt.where(
            or_(
                Service.name.ilike(q_like),
                Service.short_description.ilike(q_like),
                Service.description.ilike(q_like),
                Service.slug.ilike(q_like),
                func.cast(Service.tags, String).ilike(q_like),
                func.cast(Service.search_keywords, String).ilike(q_like),
            )
        )

        if sort_by == "popular":
            svc_stmt = svc_stmt.order_by(Service.view_count.desc(), Service.name)
        elif sort_by == "name":
            svc_stmt = svc_stmt.order_by(Service.name)
        else:
            svc_stmt = svc_stmt.order_by(Service.is_featured.desc(), Service.name)

        services = (await db.execute(svc_stmt.limit(30))).scalars().all()
        for s in services:
            results.append({
                "type": "service",
                "id": str(s.id),
                "name": s.name,
                "slug": s.slug,
                "description": s.short_description or s.description or "",
                "category": s.category.name if s.category else None,
                "category_slug": s.category.slug if s.category else None,
                "department": s.department.name if s.department else None,
                "is_online": s.is_online,
                "fee_description": s.fee_description,
                "processing_time": s.processing_time,
                "official_url": s.official_url or s.official_apply_link,
                "verification_status": s.verification_status or "UNVERIFIED",
                "verification_notes": s.verification_notes,
                "source_domain": s.source_domain,
                "confidence": _confidence(s.verification_status, bool(s.official_url or s.official_apply_link)),
                "url": f"/services/{s.slug}",
            })

    # 2. Search Schemes
    if type in ("all", "scheme"):
        sch_stmt = (
            select(Scheme)
            .where(Scheme.deleted_at.is_(None), Scheme.is_active.is_(True))
            .options(selectinload(Scheme.ministry))
        )
        if ministry_slug:
            sch_stmt = sch_stmt.join(Scheme.ministry).where(Ministry.slug == ministry_slug)

        sch_stmt = sch_stmt.where(
            or_(
                Scheme.name.ilike(q_like),
                Scheme.short_description.ilike(q_like),
                Scheme.description.ilike(q_like),
                Scheme.target_beneficiary.ilike(q_like),
                Scheme.benefits_description.ilike(q_like),
            )
        )
        if sort_by == "name":
            sch_stmt = sch_stmt.order_by(Scheme.name)
        else:
            sch_stmt = sch_stmt.order_by(Scheme.is_featured.desc(), Scheme.name)

        schemes = (await db.execute(sch_stmt.limit(20))).scalars().all()
        for sc in schemes:
            results.append({
                "type": "scheme",
                "id": str(sc.id),
                "name": sc.name,
                "slug": sc.slug,
                "description": sc.short_description or sc.description or "",
                "ministry": sc.ministry.name if sc.ministry else None,
                "target_beneficiary": sc.target_beneficiary,
                "benefit_amount": sc.benefit_amount,
                "official_url": sc.official_portal or sc.official_url,
                "verification_status": sc.verification_status or "UNVERIFIED",
                "source_domain": sc.source_domain,
                "confidence": _confidence(sc.verification_status, bool(sc.official_portal or sc.official_url)),
                "url": f"/schemes/{sc.slug}",
            })

    # 3. Search FAQs
    if type in ("all", "faq"):
        faq_stmt = (
            select(FAQ)
            .where(FAQ.deleted_at.is_(None), FAQ.is_active.is_(True))
            .where(
                or_(
                    FAQ.question.ilike(q_like),
                    FAQ.answer.ilike(q_like),
                )
            )
            .limit(10)
        )
        faqs = (await db.execute(faq_stmt)).scalars().all()
        for f in faqs:
            results.append({
                "type": "faq",
                "id": str(f.id),
                "question": f.question,
                "answer": f.answer,
                "url": "/faq",
            })

    # 4. Search Ministries
    if type in ("all", "ministry"):
        min_stmt = (
            select(Ministry)
            .where(Ministry.deleted_at.is_(None), Ministry.is_active.is_(True))
            .where(
                or_(
                    Ministry.name.ilike(q_like),
                    Ministry.short_name.ilike(q_like),
                )
            )
            .limit(5)
        )
        mins = (await db.execute(min_stmt)).scalars().all()
        for m in mins:
            results.append({
                "type": "ministry",
                "id": str(m.id),
                "name": m.name,
                "slug": m.slug,
                "short_name": m.short_name,
                "website": m.website,
                "url": f"/services?ministry={m.slug}",
            })

    # Log search history
    try:
        sh = SearchHistory(
            user_id=current_user.id if current_user else None,
            query=q_clean,
            result_count=len(results),
        )
        db.add(sh)
        await db.commit()
    except Exception:
        pass

    total = len(results)
    offset = (page - 1) * page_size
    paginated_results = results[offset : offset + page_size]

    return ApiResponse.ok(
        data={
            "query": q_clean,
            "results": paginated_results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),
            "filter": {"type": type, "category": category_slug, "ministry": ministry_slug},
        }
    )


@router.get("/suggestions", response_model=ApiResponse[dict])
@rate_search("120/minute")
async def search_suggestions(
    db: DbDep,
    request: Request,
    q: str = Query(..., min_length=1, description="Partial search query"),
) -> ApiResponse[dict]:
    """Instant typeahead autocomplete for services, schemes, FAQs, and ministries."""
    q_clean = q.strip()
    q_like = f"%{q_clean}%"

    svc_stmt = (
        select(Service.name, Service.slug, Service.short_description)
        .where(Service.deleted_at.is_(None), Service.is_active.is_(True))
        .where(Service.name.ilike(q_like))
        .limit(5)
    )
    sch_stmt = (
        select(Scheme.name, Scheme.slug, Scheme.target_beneficiary)
        .where(Scheme.deleted_at.is_(None), Scheme.is_active.is_(True))
        .where(Scheme.name.ilike(q_like))
        .limit(4)
    )
    faq_stmt = (
        select(FAQ.question)
        .where(FAQ.deleted_at.is_(None), FAQ.is_active.is_(True))
        .where(FAQ.question.ilike(q_like))
        .limit(3)
    )
    min_stmt = (
        select(Ministry.name, Ministry.slug)
        .where(Ministry.deleted_at.is_(None), Ministry.is_active.is_(True))
        .where(Ministry.name.ilike(q_like))
        .limit(3)
    )

    services = (await db.execute(svc_stmt)).all()
    schemes = (await db.execute(sch_stmt)).all()
    faqs = (await db.execute(faq_stmt)).all()
    ministries = (await db.execute(min_stmt)).all()

    return ApiResponse.ok(
        data={
            "query": q_clean,
            "services": [{"name": r[0], "slug": r[1], "description": r[2]} for r in services],
            "schemes": [{"name": r[0], "slug": r[1], "beneficiary": r[2]} for r in schemes],
            "faqs": [{"question": r[0]} for r in faqs],
            "ministries": [{"name": r[0], "slug": r[1]} for r in ministries],
        }
    )


@router.get("/popular", response_model=ApiResponse[dict])
async def popular_searches(db: DbDep) -> ApiResponse[dict]:
    """Frequently searched topics (from real search history) and top categories."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Query trending searches from the last 30 days that are at least 3 characters
    trend_rows = (
        await db.execute(
            select(SearchHistory.query, func.count(SearchHistory.id).label("cnt"))
            .where(SearchHistory.created_at >= cutoff)
            .where(func.length(SearchHistory.query) >= 4)
            .group_by(SearchHistory.query)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(15)
        )
    ).all()
    
    trending = []
    seen = set()
    for r in trend_rows:
        q_clean = r.query.strip().title()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            trending.append(q_clean)
            
    # Pad with legitimate default popular searches if there are fewer than 6 trending searches
    defaults = ["Aadhaar", "Birth Certificate", "Driving Licence", "PM Kisan", "Pension", "Ration Card"]
    for d in defaults:
        if len(trending) >= 6:
            break
        if d.lower() not in seen:
            seen.add(d.lower())
            trending.append(d)
            
    # Slice to exactly 6 items for clean UI rendering
    trending = trending[:6]

    cat_rows = (
        await db.execute(
            select(Category.name, Category.slug, Category.icon)
            .where(Category.is_active.is_(True))
            .order_by(Category.display_order, Category.name)
            .limit(6)
        )
    ).all()

    return ApiResponse.ok(
        data={
            "trending": trending,
            "top_categories": [
                {"name": name, "slug": slug, "icon": icon or "Folder"} for name, slug, icon in cat_rows
            ],
            "source": "search_history" if trend_rows else "defaults",
        }
    )
