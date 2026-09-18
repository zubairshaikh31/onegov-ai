"""
OneGov AI — Admin Panel Endpoints
Provides system KPIs, analytics data (real DB aggregations), CRUD management for
Services, Schemes, Categories, Ministries, FAQs, Users, Feedback, AI logs,
intelligence/source-monitoring overview and live provider usage.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies import CurrentUser, DbDep
from app.models.activity import AIChatHistory, Analytics, ContactMessage, Feedback, Notification, SearchHistory
from app.models.government import Category, Department, FAQ, Ministry, Scheme, Service
from app.models.intelligence import (
    CitizenJourney,
    LifeEvent,
    SourceChangeLog,
    SourceMonitor,
    UserTask,
    Video,
)
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: CurrentUser) -> User:
    if not current_user.is_admin and "admin" not in current_user.role_names:
        raise ForbiddenError("Admin privileges required.")
    return current_user


# ── 1. Admin KPI Overview ──────────────────────────────────────────────────────

@router.get("/overview", response_model=ApiResponse[dict])
async def admin_overview(
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Get system KPIs for the admin dashboard."""
    users_count = (await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))).scalar_one()
    services_count = (await db.execute(select(func.count(Service.id)).where(Service.deleted_at.is_(None)))).scalar_one()
    schemes_count = (await db.execute(select(func.count(Scheme.id)).where(Scheme.deleted_at.is_(None)))).scalar_one()
    searches_count = (await db.execute(select(func.count(SearchHistory.id)))).scalar_one()
    chats_count = (await db.execute(select(func.count(AIChatHistory.id)))).scalar_one()
    messages_count = (await db.execute(select(func.count(ContactMessage.id)))).scalar_one()

    return ApiResponse.ok(
        data={
            "stats": {
                "total_users": users_count,
                "total_services": services_count,
                "total_schemes": schemes_count,
                "total_searches": searches_count,
                "total_ai_conversations": chats_count,
                "pending_inquiries": messages_count,
            },
            "system": {
                "status": "healthy",
                "database": "PostgreSQL 16 + pgvector",
                "ai_provider": "Ollama / Llama 3.2",
                "redis": "Connected",
            },
        }
    )


# ── 2. Analytics Charts Data ──────────────────────────────────────────────────

@router.get("/analytics", response_model=ApiResponse[dict])
async def admin_analytics(
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Real DB analytics timeseries for Recharts (no mock data)."""
    now = datetime.now(timezone.utc)
    days_30 = now - timedelta(days=30)
    days_14 = now - timedelta(days=14)
    days_60 = now - timedelta(days=60)

    # Top viewed services from real analytics events (service_view)
    svc_view_rows = (
        await db.execute(
            select(
                Service.name,
                func.count(Analytics.id).label("views"),
            )
            .join(
                Analytics,
                (Analytics.entity_id == Service.id)
                & (Analytics.entity_type == "service")
                & Analytics.event_type.like("service_view%"),
            )
            .where(Service.deleted_at.is_(None))
            .group_by(Service.id, Service.name)
            .order_by(func.count(Analytics.id).desc())
            .limit(6)
        )
    ).all()
    top_services = [{"name": name, "views": int(views)} for name, views in svc_view_rows]
    # Honest fallback: stored view_count until analytics events arrive.
    if not top_services:
        fallback_rows = (
            await db.execute(
                select(Service.name, Service.view_count)
                .where(Service.deleted_at.is_(None))
                .order_by(Service.view_count.desc())
                .limit(6)
            )
        ).all()
        top_services = [{"name": r[0], "views": int(r[1] or 0)} for r in fallback_rows]

    # Popular searches from real search history (last 30 days)
    search_rows = (
        await db.execute(
            select(SearchHistory.query, func.count(SearchHistory.id).label("searches"))
            .where(SearchHistory.created_at >= days_30)
            .group_by(SearchHistory.query)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(10)
        )
    ).all()
    popular_searches = [{"name": query, "searches": int(searches)} for query, searches in search_rows]

    # AI usage per day (last 14 days), from real chat history
    ai_rows = (
        await db.execute(
            select(
                func.to_char(AIChatHistory.created_at, "YYYY-MM-DD").label("day"),
                func.count(AIChatHistory.id).label("queries"),
                func.coalesce(func.sum(AIChatHistory.tokens_used), 0).label("tokens"),
            )
            .where(AIChatHistory.created_at >= days_14)
            .group_by(func.to_char(AIChatHistory.created_at, "YYYY-MM-DD"))
            .order_by(func.to_char(AIChatHistory.created_at, "YYYY-MM-DD"))
        )
    ).all()
    ai_usage = [
        {"day": day, "queries": int(queries), "tokens": int(tokens)}
        for day, queries, tokens in ai_rows
    ]

    # User registration growth (monthly cumulative, last 60 days)
    reg_rows = (
        await db.execute(
            select(
                func.to_char(User.created_at, "YYYY-MM").label("month"),
                func.count(User.id).label("users"),
            )
            .where(User.deleted_at.is_(None), User.created_at >= days_60)
            .group_by(func.to_char(User.created_at, "YYYY-MM"))
            .order_by(func.to_char(User.created_at, "YYYY-MM"))
        )
    ).all()
    cumulative = 0
    user_growth = []
    for month, count in reg_rows:
        cumulative += int(count)
        user_growth.append({"month": month, "users": cumulative})

    return ApiResponse.ok(
        data={
            "top_services": top_services,
            "popular_searches": popular_searches,
            "ai_usage": ai_usage,
            "user_growth": user_growth,
            "window_days": {"searches": 30, "ai": 14, "users": 60},
        }
    )


# ── 2b. Intelligence / Source-Monitoring Overview ─────────────────────────────

@router.get("/intelligence/overview", response_model=ApiResponse[dict])
async def admin_intelligence_overview(
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Census for the intelligence layer: videos, journeys, life events, monitors."""
    model_counts = [
        ("total_videos", Video),
        ("total_journeys", CitizenJourney),
        ("total_life_events", LifeEvent),
        ("total_source_monitors", SourceMonitor),
        ("total_change_logs", SourceChangeLog),
        ("total_user_tasks", UserTask),
    ]
    counts: dict[str, int] = {}
    for key, model in model_counts:
        counts[key] = int((await db.execute(select(func.count(model.id)))).scalar_one())

    monitor_rows = (
        await db.execute(
            select(
                SourceMonitor.url,
                SourceMonitor.domain,
                SourceMonitor.source_type,
                SourceMonitor.status,
                SourceMonitor.last_fetched_at,
                SourceMonitor.next_fetch_at,
                SourceMonitor.retry_count,
            )
            .order_by(SourceMonitor.last_fetched_at.desc().nullslast(), SourceMonitor.domain)
            .limit(20)
        )
    ).all()
    monitors = [
        {
            "url": row[0],
            "domain": row[1],
            "source_type": row[2],
            "status": row[3],
            "last_fetched_at": row[4],
            "next_fetch_at": row[5],
            "retry_count": int(row[6] or 0),
        }
        for row in monitor_rows
    ]

    recent_change_rows = (
        await db.execute(
            select(SourceChangeLog)
            .order_by(SourceChangeLog.created_at.desc())
            .limit(10)
        )
    ).all()
    recent_changes = [
        {
            "entity_type": c.entity_type,
            "entity_id": str(c.entity_id) if c.entity_id else None,
            "entity_slug": c.entity_slug,
            "change_type": c.change_type,
            "source_url": c.source_url,
            "changed_at": c.created_at,
        }
        for c in recent_change_rows
    ]

    return ApiResponse.ok(
        data={"counts": counts, "monitors": monitors, "recent_changes": recent_changes}
    )


# ── 2c. Live AI Provider Usage ────────────────────────────────────────────────

@router.get("/ai/usage", response_model=ApiResponse[dict])
async def admin_ai_provider_usage(
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Live usage snapshot from the in-process UsageTracker."""
    from ai.services.usage import get_usage_tracker

    s = get_usage_tracker().snapshot()

    return ApiResponse.ok(
        data={
            "provider": s["provider"],
            "model": s["model"],
            "totals": {
                "calls": s["calls"],
                "embed_calls": s["embed_calls"],
                "input_tokens": s["input_tokens"],
                "output_tokens": s["output_tokens"],
                "total_tokens": s["total_tokens"],
                "errors": s["errors"],
                "error_rate": s["error_rate"],
                "avg_latency_ms": s["avg_latency_ms"],
                "est_cost_usd": s["est_cost_usd"],
                "uptime_seconds": s["uptime_seconds"],
            },
        }
    )


# ── 3. Services CRUD ──────────────────────────────────────────────────────────

class ServiceCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    category_id: UUID | None = None
    department_id: UUID | None = None
    is_online: bool = True
    is_featured: bool = False
    fee_description: str | None = None
    processing_time: str | None = None
    official_url: str | None = None


@router.post("/services", response_model=ApiResponse[dict])
async def admin_create_service(
    body: ServiceCreateRequest,
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Create a new government service."""
    svc = Service(
        name=body.name,
        slug=body.slug,
        description=body.description,
        short_description=body.short_description,
        category_id=body.category_id,
        department_id=body.department_id,
        is_online=body.is_online,
        is_featured=body.is_featured,
        fee_description=body.fee_description,
        processing_time=body.processing_time,
        official_url=body.official_url,
        is_active=True,
    )
    db.add(svc)
    await db.commit()
    await db.refresh(svc)
    return ApiResponse.ok(data=svc.to_dict(), message="Service created successfully.")


@router.delete("/services/{service_id}", response_model=ApiResponse[None])
async def admin_delete_service(
    service_id: UUID,
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[None]:
    """Soft-delete a service."""
    await db.execute(
        update(Service).where(Service.id == service_id).values(deleted_at=func.now())
    )
    await db.commit()
    return ApiResponse.ok(message="Service deleted.")


# ── 4. Schemes CRUD ───────────────────────────────────────────────────────────

class SchemeCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    target_beneficiary: str | None = None
    benefit_amount: str | None = None
    scheme_type: str = "central"
    ministry_id: UUID | None = None
    official_url: str | None = None
    is_featured: bool = False


@router.post("/schemes", response_model=ApiResponse[dict])
async def admin_create_scheme(
    body: SchemeCreateRequest,
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Create a new welfare scheme."""
    sch = Scheme(
        name=body.name,
        slug=body.slug,
        description=body.description,
        target_beneficiary=body.target_beneficiary,
        benefit_amount=body.benefit_amount,
        scheme_type=body.scheme_type,
        ministry_id=body.ministry_id,
        official_url=body.official_url,
        is_featured=body.is_featured,
        is_active=True,
    )
    db.add(sch)
    await db.commit()
    await db.refresh(sch)
    return ApiResponse.ok(data=sch.to_dict(), message="Scheme created successfully.")


@router.delete("/schemes/{scheme_id}", response_model=ApiResponse[None])
async def admin_delete_scheme(
    scheme_id: UUID,
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[None]:
    """Soft-delete a scheme."""
    await db.execute(
        update(Scheme).where(Scheme.id == scheme_id).values(deleted_at=func.now())
    )
    await db.commit()
    return ApiResponse.ok(message="Scheme deleted.")


# ── 5. Users Management ───────────────────────────────────────────────────────

@router.get("/users", response_model=ApiResponse[dict])
async def admin_list_users(
    db: DbDep,
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """List registered users with status and roles."""
    stmt = (
        select(User)
        .where(User.deleted_at.is_(None))
        .options(selectinload(User.roles))
        .order_by(User.created_at.desc())
    )
    if q:
        stmt = stmt.where(or_(User.email.ilike(f"%{q}%"), User.full_name.ilike(f"%{q}%")))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    items = []
    for u in rows:
        d = u.to_dict()
        d["roles"] = [r.name for r in u.roles]
        items.append(d)

    return ApiResponse.ok(
        data={"items": items, "total": total, "page": page, "page_size": page_size}
    )


@router.post("/users/{user_id}/toggle-status", response_model=ApiResponse[None])
async def admin_toggle_user_status(
    user_id: UUID,
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[None]:
    """Toggle user active / suspended status."""
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found.")

    user.is_active = not user.is_active
    await db.commit()
    return ApiResponse.ok(message=f"User marked as {'active' if user.is_active else 'suspended'}.")


# ── 6. AI Conversation Logs ───────────────────────────────────────────────────

@router.get("/ai-logs", response_model=ApiResponse[dict])
async def admin_ai_logs(
    db: DbDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """View recent citizen AI chat history logs."""
    stmt = (
        select(AIChatHistory)
        .where(AIChatHistory.deleted_at.is_(None))
        .order_by(AIChatHistory.created_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return ApiResponse.ok(
        data={"items": [r.to_dict() for r in rows], "total": total, "page": page, "page_size": page_size}
    )


# ── 7. Feedback & Inquiries ───────────────────────────────────────────────────

@router.get("/feedback", response_model=ApiResponse[dict])
async def admin_feedback_list(
    db: DbDep,
    admin_user: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """View citizen contact inquiries and feedback."""
    stmt = select(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(50)
    messages = (await db.execute(stmt)).scalars().all()
    return ApiResponse.ok(data={"items": [m.to_dict() for m in messages]})
