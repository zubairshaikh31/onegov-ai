"""
OneGov AI — Intelligence Endpoints.

Discovery, deterministic eligibility, citizen journeys, life events, task
planner, service readiness, Service Radar (change tracker), service
comparator, nearby offices, video library and the source graph.

All endpoints are fully database-backed and honest: when a table is empty
(e.g. videos / change logs before their sync jobs have run) the API returns
empty lists — never fabricated data.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import CurrentUser, DbDep, OptionalCurrentUser
from app.models.activity import Analytics, GovernmentOffice
from app.models.government import (
    ApplicationStep,
    FAQ,
    Keyword,
    Scheme,
    Service,
    ServiceRelation,
)
from app.models.intelligence import (
    CitizenJourney,
    EligibilityRule,
    JourneyStep,
    LifeEvent,
    ServiceVideo,
    SourceChangeLog,
    SourceMonitor,
    UserTask,
    VerificationStatus as VStatus,
    Video,
)
from app.schemas.common import ApiResponse
from app.schemas.intelligence import (
    EligibilityCheckRequest,
    TaskPlannerRequest,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

VERIFIED_LEVELS = {VStatus.VERIFIED, VStatus.PARTIALLY_VERIFIED}


def _ok(data: object, message: str = "Success") -> ApiResponse[object]:
    return ApiResponse.ok(data=data, message=message)


def _serialize_service(svc: Service) -> dict:
    return {
        "id": str(svc.id),
        "name": svc.name,
        "name_hi": svc.name_hi,
        "slug": svc.slug,
        "description": svc.description,
        "short_description": svc.short_description,
        "category_id": str(svc.category_id) if svc.category_id else None,
        "department_id": str(svc.department_id) if svc.department_id else None,
        "official_url": svc.official_url,
        "helpline_number": svc.helpline_number,
        "email": svc.email,
        "processing_time": svc.processing_time,
        "processing_days_min": svc.processing_days_min,
        "processing_days_max": svc.processing_days_max,
        "is_online": svc.is_online,
        "is_offline": svc.is_offline,
        "service_mode": svc.service_mode,
        "service_status": svc.service_status,
        "government_level": svc.government_level,
        "state_id": svc.state_id,
        "verification_status": svc.verification_status,
        "verification_score": svc.verification_score,
        "verification_notes": svc.verification_notes,
        "source_domain": svc.source_domain,
        "source_type": svc.source_type,
        "source_last_checked": svc.source_last_checked.isoformat() if svc.source_last_checked else None,
        "is_featured": svc.is_featured,
        "tags": svc.tags,
        "is_faq": False,
    }


def _serialize_scheme(sch: Scheme) -> dict:
    return {
        "id": str(sch.id),
        "name": sch.name,
        "name_hi": sch.name_hi,
        "slug": sch.slug,
        "description": sch.description,
        "short_description": sch.short_description,
        "scheme_type": sch.scheme_type,
        "government_level": sch.government_level,
        "state_name": sch.state_name,
        "target_beneficiary": sch.target_beneficiary,
        "benefit_amount": sch.benefit_amount,
        "eligibility_description": sch.eligibility_description,
        "benefits_description": sch.benefits_description,
        "official_url": sch.official_url,
        "official_portal": sch.official_portal,
        "application_deadline": sch.application_deadline,
        "required_documents": sch.required_documents,
        "verification_status": sch.verification_status,
        "verification_score": sch.verification_score,
        "source_domain": sch.source_domain,
        "source_type": sch.source_type,
        "is_featured": sch.is_featured,
        "tags": sch.tags,
    }


# ── 1. Discovery Engine ───────────────────────────────────────────────────────

@router.get("/discovery/suggestions")
async def discovery_suggestions(
    db: DbDep,
    limit: int = Query(12, ge=1, le=50),
) -> ApiResponse[object]:
    """Personalised/general discovery: featured, trending, life events, journeys."""
    featured_stmt = (
        select(Service)
        .where(
            Service.deleted_at.is_(None),
            Service.is_active.is_(True),
            Service.is_featured.is_(True),
        )
        .order_by(Service.verification_status.desc(), Service.name)
        .limit(limit)
    )
    featured = (await db.execute(featured_stmt)).scalars().all()

    # Trending = most-viewed services (from analytics), joined to live services.
    view_counts = (
        select(Analytics.entity_id, func.count(Analytics.id).label("views"))
        .where(
            Analytics.event_type == "service_view",
            Analytics.entity_type == "service",
            Analytics.entity_id.is_not(None),
        )
        .group_by(Analytics.entity_id)
        .order_by(func.count(Analytics.id).desc())
        .limit(limit)
    )
    trend_rows = (await db.execute(view_counts)).all()
    trending = []
    if trend_rows:
        ids = [r.entity_id for r in trend_rows]
        trend_services = (
            await db.execute(
                select(Service).where(Service.id.in_(ids), Service.is_active.is_(True))
            )
        ).scalars().all()
        by_id = {s.id: s for s in trend_services}
        for r in trend_rows:
            svc = by_id.get(r.entity_id)
            if svc:
                item = _serialize_service(svc)
                item["view_count"] = r.views
                trending.append(item)

    journey_rows = (
        await db.execute(
            select(CitizenJourney).where(CitizenJourney.is_active.is_(True)).limit(6)
        )
    ).scalars().all()
    event_rows = (
        await db.execute(
            select(LifeEvent).where(LifeEvent.is_active.is_(True)).limit(6)
        )
    ).scalars().all()

    return _ok(
        {
            "featured": [_serialize_service(s) for s in featured],
            "trending": trending,
            "journeys": [
                {"slug": j.slug, "name": j.name, "description": j.description, "icon": j.icon}
                for j in journey_rows
            ],
            "life_events": [
                {"slug": e.slug, "name": e.name, "description": e.description, "icon": e.icon}
                for e in event_rows
            ],
        },
        message="Discovery suggestions",
    )


# ── 2. Life Events ────────────────────────────────────────────────────────────

@router.get("/life-events")
async def list_life_events(db: DbDep) -> ApiResponse[object]:
    """All life events, enriched with matching service/scheme names."""
    rows = (await db.execute(select(LifeEvent).where(LifeEvent.is_active.is_(True)))).scalars().all()
    events = []
    for e in rows:
        svc_slugs = list((e.service_slugs or [])[:8])
        sch_slugs = list((e.scheme_slugs or [])[:8])
        svc_names = {}
        if svc_slugs:
            svc_result = await db.execute(
                select(Service.slug, Service.name).where(Service.slug.in_(svc_slugs))
            )
            svc_names = {slug: name for slug, name in svc_result.all()}
        events.append(
            {
                "slug": e.slug,
                "name": e.name,
                "description": e.description,
                "icon": e.icon,
                "keywords": e.keywords or [],
                "services": [
                    {"slug": s, "name": svc_names.get(s, s)} for s in svc_slugs
                ],
                "schemes": sch_slugs,
            }
        )
    return _ok({"items": events}, message="Life events")


@router.get("/life-events/{slug}")
async def get_life_event(slug: str, db: DbDep) -> ApiResponse[object]:
    row = (
        await db.execute(
            select(LifeEvent).where(LifeEvent.slug == slug, LifeEvent.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Life event not found.")
    svc_slugs = list((row.service_slugs or [])[:20])
    sch_slugs = list((row.scheme_slugs or [])[:20])
    services = []
    if svc_slugs:
        svc_rows = (
            await db.execute(select(Service).where(Service.slug.in_(svc_slugs)))
        ).scalars().all()
        services = [_serialize_service(s) for s in svc_rows]
    schemes = []
    if sch_slugs:
        sch_rows = (
            await db.execute(select(Scheme).where(Scheme.slug.in_(sch_slugs)))
        ).scalars().all()
        schemes = [_serialize_scheme(s) for s in sch_rows]
    return _ok(
        {
            "slug": row.slug,
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "keywords": row.keywords or [],
            "services": services,
            "schemes": schemes,
        },
        message="Life event",
    )


# ── 3. Citizen Journeys ───────────────────────────────────────────────────────

@router.get("/journeys")
async def list_journeys(db: DbDep) -> ApiResponse[object]:
    """All citizen journeys with their ordered steps."""
    rows = (
        await db.execute(
            select(CitizenJourney)
            .where(CitizenJourney.is_active.is_(True))
            .options(selectinload(CitizenJourney.steps))
            .order_by(CitizenJourney.name)
        )
    ).scalars().all()
    return _ok(
        {
            "items": [
                {
                    "slug": j.slug,
                    "name": j.name,
                    "description": j.description,
                    "icon": j.icon,
                    "keywords": j.keywords or [],
                    "steps": [
                        {
                            "step_number": s.step_number,
                            "title": s.title,
                            "description": s.description,
                            "target_type": s.target_type,
                            "target_slug": s.target_slug,
                            "duration_estimate": s.duration_estimate,
                            "is_optional": s.is_optional,
                        }
                        for s in j.steps
                    ],
                }
                for j in rows
            ]
        },
        message="Citizen journeys",
    )


@router.get("/journeys/{slug}")
async def get_journey(slug: str, db: DbDep) -> ApiResponse[object]:
    row = (
        await db.execute(
            select(CitizenJourney)
            .where(CitizenJourney.slug == slug, CitizenJourney.is_active.is_(True))
            .options(selectinload(CitizenJourney.steps))
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Journey not found.")
    return _ok(
        {
            "slug": row.slug,
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "keywords": row.keywords or [],
            "steps": [
                {
                    "step_number": s.step_number,
                    "title": s.title,
                    "description": s.description,
                    "target_type": s.target_type,
                    "target_slug": s.target_slug,
                    "duration_estimate": s.duration_estimate,
                    "is_optional": s.is_optional,
                }
                for s in row.steps
            ],
        },
        message="Citizen journey",
    )


# ── 4. Deterministic Eligibility Engine ───────────────────────────────────────

def _coerce(value: object) -> object:
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"", "n/a", "na", "not available", "none", "unknown", "not sure", "not known"}:
            return None
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return float(s) if "." in s else int(s)
        return s
    return value


def _evaluate_rule(rule: EligibilityRule, criteria: dict[str, object]) -> dict:
    provided = criteria.get(rule.field)
    provided = _coerce(provided)
    expected = rule.value

    if provided is None:
        return {
            "field": rule.field,
            "operator": rule.operator,
            "provided": None,
            "passed": None,  # indeterminate — missing input
            "explanation": rule.explanation or f"Information for '{rule.field}' was not provided.",
        }

    passed: bool | None = False
    match rule.operator:
        case "eq":
            passed = provided == expected
        case "neq":
            passed = provided != expected
        case "gt":
            passed = all(isinstance(a, (int, float)) and isinstance(b, (int, float)) for a, b in [(provided, expected)]) and float(provided) > float(expected)  # type: ignore[arg-type]
        case "gte":
            passed = all(isinstance(a, (int, float)) and isinstance(b, (int, float)) for a, b in [(provided, expected)]) and float(provided) >= float(expected)  # type: ignore[arg-type]
        case "lt":
            passed = all(isinstance(a, (int, float)) and isinstance(b, (int, float)) for a, b in [(provided, expected)]) and float(provided) < float(expected)  # type: ignore[arg-type]
        case "lte":
            passed = all(isinstance(a, (int, float)) and isinstance(b, (int, float)) for a, b in [(provided, expected)]) and float(provided) <= float(expected)  # type: ignore[arg-type]
        case "in":
            passed = provided in (expected if isinstance(expected, list) else [expected])
        case "not_in":
            passed = provided not in (expected if isinstance(expected, list) else [expected])
        case "contains":
            if isinstance(provided, str):
                passed = str(expected).lower() in provided
            elif isinstance(provided, list):
                passed = provided in (expected if isinstance(expected, list) else [expected])
            else:
                passed = False
        case "between":
            if isinstance(expected, list) and len(expected) == 2 and isinstance(provided, (int, float)):
                lo, hi = expected[0], expected[1]
                passed = all(isinstance(x, (int, float)) for x in (lo, hi)) and float(lo) <= float(provided) <= float(hi)  # type: ignore[arg-type]
            else:
                passed = False
        case _:
            passed = None

    return {
        "field": rule.field,
        "operator": rule.operator,
        "provided": provided,
        "expected": expected,
        "passed": passed,
        "explanation": rule.explanation,
    }


@router.post("/eligibility/check")
async def eligibility_check(payload: EligibilityCheckRequest, db: DbDep) -> ApiResponse[object]:
    """Deterministic eligibility check against stored rules (or honest heuristic)."""
    model = Service if payload.entity_type == "service" else Scheme
    entity = (
        await db.execute(
            select(model).where(model.slug == payload.entity_slug, model.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if entity is None:
        raise NotFoundError(f"{payload.entity_type} '{payload.entity_slug}' not found.")

    rules = (
        await db.execute(
            select(EligibilityRule)
            .where(
                EligibilityRule.entity_type == payload.entity_type,
                EligibilityRule.entity_id == entity.id,
            )
            .order_by(EligibilityRule.priority, EligibilityRule.field)
        )
    ).scalars().all()

    if not rules:
        return _heuristic_eligibility(payload, entity)

    results = [_evaluate_rule(r, payload.criteria) for r in rules]
    missing = [r for r in results if r["passed"] is None]
    failed = [r for r in results if r["passed"] is False]
    passed = [r for r in results if r["passed"] is True]

    if failed:
        verdict = "NOT_ELIGIBLE"
    elif missing:
        verdict = "MORE_INFO_REQUIRED"
    else:
        verdict = "ELIGIBLE"

    confidence = max(0.0, min(1.0, len(passed) / max(1, len(results))))

    unmet = [
        {
            "field": r["field"],
            "operator": r["operator"],
            "provided": r["provided"],
            "expected": r.get("expected"),
            "explanation": r["explanation"],
        }
        for r in failed if r.get("expected") is not None
    ] or [
        {"field": r["field"], "explanation": r["explanation"]}
        for r in failed
    ]

    return _ok(
        {
            "entity_type": payload.entity_type,
            "entity_slug": payload.entity_slug,
            "entity_name": entity.name,
            "verdict": verdict,
            "passed": passed,
            "unmet": unmet,
            "missing": [
                {"field": r["field"], "explanation": r["explanation"]} for r in missing
            ],
            "confidence": round(confidence, 2),
            "overall_explanation": (
                "You meet all checked criteria."
                if verdict == "ELIGIBLE"
                else ("Some criteria could not be verified from the information provided."
                      if verdict == "MORE_INFO_REQUIRED"
                      else "You do not meet one or more eligibility criteria based on the information provided.")
            ),
        },
        message="Eligibility check",
    )


def _heuristic_eligibility(payload: EligibilityCheckRequest, entity: object) -> ApiResponse[object]:
    """No structured rules yet — surface the official eligibility text honestly."""
    if payload.entity_type == "service":
        text = getattr(entity, "eligibility_description") or getattr(entity, "description") or ""
    else:
        text = getattr(entity, "eligibility_description") or getattr(entity, "benefits_description") or ""
    return _ok(
        {
            "entity_type": payload.entity_type,
            "entity_slug": payload.entity_slug,
            "entity_name": getattr(entity, "name"),
            "verdict": "REVIEW_REQUIRED",
            "passed": [],
            "unmet": [],
            "missing": [],  # type: ignore[list-item]
            "provided_criteria": payload.criteria,
            "confidence": 0.3,
            "mode": "heuristic",
            "overall_explanation": (
                "Structured eligibility rules are not yet published for this item. "
                "Review the official eligibility description below to confirm."
            ),
            "official_eligibility_text": text[:4000],
        },
        message="Eligibility check (heuristic)",
    )


# ── 5. Task Planner & Task Board ──────────────────────────────────────────────

@router.post("/tasks/planner")
async def planner(payload: TaskPlannerRequest, db: DbDep, user: CurrentUser) -> ApiResponse[object]:
    """Generate a citizen's personalised government task board."""
    tasks: list[dict] = []

    if payload.journey_slug:
        journey = (
            await db.execute(
                select(CitizenJourney).where(CitizenJourney.slug == payload.journey_slug, CitizenJourney.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if journey is None:
            raise NotFoundError("Journey not found.")
        steps = (
            await db.execute(
                select(JourneyStep)
                .where(JourneyStep.journey_id == journey.id)
                .order_by(JourneyStep.step_number)
            )
        ).scalars().all()
        for step in steps:
            tasks.append(
                {
                    "entity_type": step.target_type,
                    "entity_id": step.target_id,
                    "entity_slug": step.target_slug,
                    "title": step.title,
                    "description": step.description,
                    "estimated_effort": step.duration_estimate,
                    "priority": "HIGH" if step.step_number == 1 else "MEDIUM",
                }
            )

    if payload.service_slugs:
        svc_rows = (
            await db.execute(select(Service).where(Service.slug.in_(payload.service_slugs), Service.is_active.is_(True)))
        ).scalars().all()
        for svc in svc_rows:
            steps = (
                await db.execute(
                    select(ApplicationStep)
                    .where(ApplicationStep.service_id == svc.id)
                    .order_by(ApplicationStep.step_number)
                )
            ).scalars().all()
            if steps:
                for s in steps:
                    tasks.append(
                        {
                            "entity_type": "service",
                            "entity_id": svc.id,
                            "entity_slug": svc.slug,
                            "title": f"{svc.name}: {s.title}",
                            "description": s.description,
                            "estimated_effort": s.estimated_time,
                            "priority": "HIGH" if s.step_number <= 1 else "MEDIUM",
                            "external_url": s.action_url or svc.official_url,
                        }
                    )
            else:
                tasks.append(
                    {
                        "entity_type": "service",
                        "entity_id": svc.id,
                        "entity_slug": svc.slug,
                        "title": f"Apply for {svc.name}",
                        "description": "Complete the application on the official portal.",
                        "priority": "HIGH",
                        "external_url": svc.official_url or svc.official_apply_link,
                    }
                )

    created: list[dict] = []
    for task in tasks:
        tr = UserTask(
            user_id=user.id,
            entity_type=task["entity_type"],
            entity_id=task["entity_id"],
            entity_slug=task["entity_slug"],
            title=task["title"],
            notes=task.get("description"),
            priority=task["priority"],
            estimated_effort=task.get("estimated_effort"),
            external_url=task.get("external_url"),
        )
        db.add(tr)
        await db.flush()
        created.append(
            {
                "id": str(tr.id),
                "title": tr.title,
                "entity_type": tr.entity_type,
                "entity_slug": tr.entity_slug,
                "status": tr.status,
                "priority": tr.priority,
                "external_url": tr.external_url,
            }
        )

    return _ok({"created": created, "count": len(created)}, message="Tasks generated")


@router.get("/tasks")
async def list_tasks(
    db: DbDep,
    user: OptionalCurrentUser,
    status: str | None = Query(None),
    priority: str | None = Query(None),
) -> ApiResponse[object]:
    """The user's government task board."""
    if user is None:
        return _ok({"items": [], "message": "Sign in to view your task board."})
    stmt = select(UserTask).where(UserTask.user_id == user.id, UserTask.deleted_at.is_(None))
    if status:
        stmt = stmt.where(UserTask.status == status.upper())
    if priority:
        stmt = stmt.where(UserTask.priority == priority.upper())
    stmt = stmt.order_by(UserTask.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return _ok(
        {
            "items": [
                {
                    "id": str(t.id),
                    "entity_type": t.entity_type,
                    "entity_slug": t.entity_slug,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "notes": t.notes,
                    "estimated_effort": t.estimated_effort,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "external_url": t.external_url,
                    "created_at": t.created_at.isoformat(),
                }
                for t in rows
            ]
        },
        message="Task board",
    )


@router.patch("/tasks/{task_id}")
async def update_task(task_id: UUID, payload: TaskUpdateRequest, db: DbDep, user: CurrentUser) -> ApiResponse[object]:
    task = (
        await db.execute(
            select(UserTask).where(UserTask.id == task_id, UserTask.user_id == user.id, UserTask.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if task is None:
        raise NotFoundError("Task not found.")
    if payload.status:
        task.status = payload.status
    if payload.priority:
        task.priority = payload.priority
    if payload.notes is not None:
        task.notes = payload.notes
    await db.commit()
    return _ok({"id": str(task.id), "status": task.status, "priority": task.priority}, message="Task updated")


# ── 6. Service / Scheme Readiness ─────────────────────────────────────────────

@router.get("/readiness/{entity_type}/{entity_slug}")
async def readiness(
    entity_type: str,
    entity_slug: str,
    db: DbDep,
) -> ApiResponse[object]:
    """Readiness score: how complete/actionable a service or scheme is."""
    model = Service if entity_type == "service" else Scheme
    entity = (
        await db.execute(
            select(model).where(model.slug == entity_slug, model.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if entity is None:
        raise NotFoundError(f"{entity_type} '{entity_slug}' not found.")

    verification = (entity.verification_status or VStatus.UNVERIFIED).upper()
    has_url = bool((getattr(entity, "official_url", None) or getattr(entity, "official_portal", None)))
    has_contact = bool(getattr(entity, "helpline_number", None) or getattr(entity, "email", None))
    has_eligibility = bool(getattr(entity, "eligibility_description", None))
    processing = bool(
        getattr(entity, "processing_days_min", None)
        or getattr(entity, "processing_days_max", None)
        or getattr(entity, "processing_time", None)
    )
    status_active = (getattr(entity, "service_status", None) or "ACTIVE") == "ACTIVE"

    checklist = [
        {"item": "Verification status", "achieved": verification in VERIFIED_LEVELS,
         "detail": verification.title().replace("_", " ")},
        {"item": "Official portal link", "achieved": has_url,
         "detail": "Link to official portal present" if has_url else "No official portal link recorded"},
        {"item": "Help / contact channel", "achieved": has_contact,
         "detail": "Helpline or email present" if has_contact else "No helpline/email recorded"},
        {"item": "Eligibility details", "achieved": has_eligibility,
         "detail": "Eligibility described" if has_eligibility else "No eligibility description"},
        {"item": "Processing time", "achieved": processing,
         "detail": "Expected processing time recorded" if processing else "No processing time recorded"},
        {"item": "Service status active", "achieved": status_active,
         "detail": getattr(entity, "service_status", "ACTIVE") if not status_active else "Active"},
    ]

    weights = [40.0, 20.0, 15.0, 10.0, 10.0, 5.0]
    score = round(sum(w for w, c in zip(weights, checklist) if c["achieved"]), 1)

    return _ok(
        {
            "entity_type": entity_type,
            "entity_slug": entity_slug,
            "entity_name": entity.name,
            "score": score,
            "status": "READY" if score >= 75 else ("PARTIALLY_READY" if score >= 40 else "NEEDS_ATTENTION"),
            "verification_status": verification,
            "checklist": checklist,
            "known_gaps": [
                c["item"] for c in checklist if not c["achieved"]
            ],
            "disclaimer": "Readiness is computed from recorded data quality, not a guarantee of service.",
        },
        message="Readiness",
    )


# ── 7. Service Radar / Change Tracker ─────────────────────────────────────────

@router.get("/radar/changes")
async def radar_changes(
    db: DbDep,
    entity_type: str | None = Query(None),
    verified_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[object]:
    """Recent detected changes on official sources (Service Radar)."""
    stmt = (
        select(SourceChangeLog)
        .order_by(SourceChangeLog.created_at.desc(), SourceChangeLog.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    filters = [SourceChangeLog.processed.is_(True)]
    if entity_type:
        filters.append(SourceChangeLog.entity_type == entity_type)
    if verified_only:
        filters.append(SourceChangeLog.verification_status.in_(VERIFIED_LEVELS))
    stmt = stmt.where(*filters)
    rows = (await db.execute(stmt)).scalars().all()

    total = (
        await db.execute(
            select(func.count()).select_from(SourceChangeLog).where(*filters)
        )
    ).scalar_one()

    return _ok(
        {
            "items": [
                {
                    "id": str(c.id),
                    "entity_type": c.entity_type,
                    "entity_slug": c.entity_slug,
                    "change_type": c.change_type,
                    "source_url": c.source_url,
                    "diff_summary": c.diff_summary,
                    "verification_status": c.verification_status,
                    "detected_at": c.created_at.isoformat(),
                }
                for c in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Service radar changes",
    )


@router.get("/radar/sources")
async def radar_sources(db: DbDep) -> ApiResponse[object]:
    """Snapshot of monitored official sources and their health."""
    rows = (
        await db.execute(select(SourceMonitor).order_by(SourceMonitor.domain, SourceMonitor.url))
    ).scalars().all()

    status_counts: dict[str, int] = {}
    for m in rows:
        key = m.status or "UNKNOWN"
        status_counts[key] = status_counts.get(key, 0) + 1

    return _ok(
        {
            "total_monitored": len(rows),
            "status_counts": status_counts,
            "items": [
                {
                    "id": str(m.id),
                    "url": m.url,
                    "domain": m.domain,
                    "source_type": m.source_type,
                    "entity_type": m.entity_type,
                    "entity_slug": None,
                    "status": m.status,
                    "last_status_code": m.last_status_code,
                    "last_fetched_at": m.last_fetched_at.isoformat() if m.last_fetched_at else None,
                    "next_fetch_at": m.next_fetch_at.isoformat() if m.next_fetch_at else None,
                    "retry_count": m.retry_count,
                    "robots_ok": m.robots_ok,
                }
                for m in rows[:100]
            ],
        },
        message="Source monitor snapshot",
    )


# ── 8. Comparator ─────────────────────────────────────────────────────────────

_COMPARE_FIELDS_SERVICE = [
    ("name", "name"), ("official_url", "official_url"), ("government_level", "government_level"),
    ("is_online", "is_online"), ("is_offline", "is_offline"), ("service_mode", "service_mode"),
    ("processing_time", "processing_time"), ("processing_days_min", "processing_days_min"),
    ("processing_days_max", "processing_days_max"), ("fee_description", "fee_description"),
    ("fee_amount", "fee_amount"), ("eligibility_description", "eligibility_description"),
    ("helpline_number", "helpline_number"), ("email", "email"),
    ("verification_status", "verification_status"), ("verification_score", "verification_score"),
    ("source_domain", "source_domain"),
]
_COMPARE_FIELDS_SCHEME = [
    ("name", "name"), ("official_portal", "official_portal"), ("government_level", "government_level"),
    ("target_beneficiary", "target_beneficiary"), ("benefit_amount", "benefit_amount"),
    ("eligibility_description", "eligibility_description"), ("benefits_description", "benefits_description"),
    ("application_deadline", "application_deadline"), ("verification_status", "verification_status"),
    ("source_domain", "source_domain"),
]


@router.get("/comparator")
async def comparator(
    db: DbDep,
    slugs: str = Query(..., description="Comma-separated entity slugs, e.g. aadhaar,pan,passport"),
    entity_type: str = Query("service", pattern="^(service|scheme)$"),
) -> ApiResponse[object]:
    """Side-by-side comparison of services or schemes."""
    slug_list = [s.strip() for s in slugs.split(",") if s.strip()]
    if len(slug_list) < 2:
        raise HTTPException(status_code=422, detail="Provide at least two slugs to compare.")
    slug_list = slug_list[:6]

    model = Service if entity_type == "service" else Scheme
    rows = (await db.execute(select(model).where(model.slug.in_(slug_list)))).scalars().all()
    by_slug = {getattr(r, "slug"): r for r in rows}
    fields = _COMPARE_FIELDS_SERVICE if entity_type == "service" else _COMPARE_FIELDS_SCHEME

    missing = [s for s in slug_list if s not in by_slug]
    columns = [by_slug[s] for s in slug_list if s in by_slug]

    rows_out = []
    for label, attr in fields:
        rows_out.append(
            {
                "field": label,
                "values": [getattr(c, attr) for c in columns],
            }
        )

    return _ok(
        {
            "entity_type": entity_type,
            "slugs": [getattr(c, "slug") for c in columns],
            "missing": missing,
            "row_count": len(rows_out),
            "rows": rows_out,
        },
        message="Comparator",
    )


# ── 9. Nearby / Offices ───────────────────────────────────────────────────────

@router.get("/nearby")
async def nearby(
    db: DbDep,
    q: str | None = Query(None, description="Free-text search"),
    state: str | None = Query(None),
    city: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[object]:
    """Find physical government offices / service locators."""
    stmt = select(GovernmentOffice).where(GovernmentOffice.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                GovernmentOffice.name.ilike(like),
                GovernmentOffice.address.ilike(like),
                GovernmentOffice.city.ilike(like),
                GovernmentOffice.state.ilike(like),
            )
        )
    if state:
        stmt = stmt.where(GovernmentOffice.state.ilike(f"%{state.strip()}%"))
    if city:
        stmt = stmt.where(GovernmentOffice.city.ilike(f"%{city.strip()}%"))
    stmt = stmt.order_by(GovernmentOffice.state, GovernmentOffice.city, GovernmentOffice.name).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return _ok(
        {
            "items": [
                {
                    "id": str(o.id),
                    "name": o.name,
                    "address": o.address,
                    "city": o.city,
                    "state": o.state,
                    "pincode": o.pincode,
                    "phone": o.phone,
                    "email": o.email,
                    "website": o.website,
                    "latitude": float(o.latitude) if o.latitude is not None else None,
                    "longitude": float(o.longitude) if o.longitude is not None else None,
                    "working_hours": o.working_hours,
                }
                for o in rows
            ],
            "count": len(rows),
        },
        message="Nearby offices",
    )


# ── 10. Video Library ─────────────────────────────────────────────────────────

@router.get("/videos")
async def videos(
    db: DbDep,
    service_slug: str | None = Query(None),
    language: str | None = Query(None),
    official_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[object]:
    """Educational / tutorial videos linked to government services."""
    filters = [Video.is_active.is_(True)]
    if language:
        filters.append(Video.language == language)
    if official_only:
        filters.append(Video.official_channel.is_(True))

    if service_slug:
        svc = (
            await db.execute(select(Service).where(Service.slug == service_slug))
        ).scalar_one_or_none()
        if svc is None:
            raise NotFoundError("Service not found.")
        link_rows = (
            await db.execute(
                select(ServiceVideo, Video)
                .join(Video, Video.id == ServiceVideo.video_id)
                .where(ServiceVideo.service_id == svc.id, *filters)
                .order_by(ServiceVideo.is_primary.desc(), ServiceVideo.relevance_score.desc())
                .limit(limit)
            )
        ).all()
        items = [
            _video_payload(v, svc.name)
            for _, v in link_rows
        ]
        return _ok({"service_slug": svc.slug, "items": items}, message="Service videos")

    rows = (
        await db.execute(
            select(Video).where(*filters).order_by(Video.relevance_score.desc()).limit(limit)
        )
    ).scalars().all()
    return _ok({"items": [_video_payload(v) for v in rows]}, message="Video library")


def _video_payload(v: Video, service_name: str | None = None) -> dict:
    return {
        "id": str(v.id),
        "youtube_video_id": v.youtube_video_id,
        "youtube_url": v.youtube_url,
        "title": v.title,
        "description": v.description,
        "channel_name": v.channel_name,
        "channel_url": v.channel_url,
        "thumbnail_url": v.thumbnail_url,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "duration_seconds": v.duration_seconds,
        "view_count": v.view_count,
        "language": v.language,
        "official_channel": v.official_channel,
        "verification_status": v.verification_status,
        "related_service": service_name,
    }


# ── 11. Source Graph ──────────────────────────────────────────────────────────

@router.get("/source-graph")
async def source_graph(db: DbDep) -> ApiResponse[object]:
    """Aggregate view of official sources backing the services & schemes."""
    svc_rows = (
        await db.execute(
            select(
                Service.source_domain,
                func.count(Service.id).label("count"),
                func.count(func.nullif(Service.verification_status, VStatus.UNVERIFIED)).label("verified"),
            )
            .where(Service.source_domain.is_not(None))
            .group_by(Service.source_domain)
            .order_by(func.count(Service.id).desc())
        )
    ).all()
    sch_rows = (
        await db.execute(
            select(
                Scheme.source_domain,
                func.count(Scheme.id).label("count"),
                func.count(func.nullif(Scheme.verification_status, VStatus.UNVERIFIED)).label("verified"),
            )
            .where(Scheme.source_domain.is_not(None))
            .group_by(Scheme.source_domain)
            .order_by(func.count(Scheme.id).desc())
        )
    ).all()

    domains: dict[str, dict] = {}
    for domain, count, verified in svc_rows:
        entry = domains.setdefault(domain, {"services": 0, "schemes": 0, "verified": 0})
        entry["services"] += count
        entry["verified"] += verified
    for domain, count, verified in sch_rows:
        entry = domains.setdefault(domain, {"services": 0, "schemes": 0, "verified": 0})
        entry["schemes"] += count
        entry["verified"] += verified

    total = sum(e["services"] + e["schemes"] for e in domains.values())
    return _ok(
        {
            "total_entities": total,
            "domain_count": len(domains),
            "domains": [
                {"domain": d, **counts}
                for d, counts in sorted(domains.items(), key=lambda x: -(x[1]["services"] + x[1]["schemes"]))
            ],
        },
        message="Source graph",
    )