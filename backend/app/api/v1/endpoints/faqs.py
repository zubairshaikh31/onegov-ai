"""
OneGov AI — FAQs Endpoints
"""

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.dependencies import DbDep
from app.models.government import FAQ
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/faqs", tags=["FAQs"])


@router.get("", response_model=ApiResponse[dict])
async def list_faqs(
    db: DbDep,
    q: str | None = Query(None, description="Search question or answer"),
    entity_type: str | None = Query(None, description="'service', 'scheme', or 'general'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
) -> ApiResponse[dict]:
    """Retrieve and search government service and welfare scheme FAQs."""
    stmt = select(FAQ).where(FAQ.deleted_at.is_(None), FAQ.is_active.is_(True))

    if q:
        q_like = f"%{q.strip()}%"
        stmt = stmt.where(or_(FAQ.question.ilike(q_like), FAQ.answer.ilike(q_like)))

    if entity_type:
        stmt = stmt.where(FAQ.entity_type == entity_type)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size).order_by(FAQ.display_order, FAQ.question)
    faqs = (await db.execute(stmt)).scalars().all()

    return ApiResponse.ok(
        data={
            "items": [f.to_dict() for f in faqs],
            "page": page,
            "page_size": page_size,
        }
    )
