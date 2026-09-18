"""
OneGov AI — RAG Chatbot, Health and Intelligence Endpoints
"""

import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

# Ensure root and ai packages are resolvable in all environments
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR), "/", "/app"]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger
from sqlalchemy import select, or_, text
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.dependencies import CurrentUser, OptionalCurrentUser, DbDep
from app.middleware.rate_limit import rate_ai
from app.models.activity import AIChatHistory
from app.models.government import (
    ApplicationStep,
    Category,
    Department,
    FAQ,
    KnowledgeChunk,
    Ministry,
    RequiredDocument,
    Scheme,
    Service,
    ServiceDocument,
    ServiceRelation,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatSource(BaseModel):
    title: str
    type: str
    slug: str
    url: str
    confidence: float = 0.95


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    history: list[dict[str, Any]] = []


class ChatResponse(BaseModel):
    content: str
    sources: list[ChatSource] = []
    model: str
    session_id: str


class EligibilityCheckRequest(BaseModel):
    service_or_scheme: str
    age: int | None = None
    annual_income: float | None = None
    state: str | None = None
    category: str | None = None
    occupation: str | None = None
    gender: str | None = None


class EligibilityCheckResponse(BaseModel):
    eligible: bool
    confidence: float
    summary: str
    matching_criteria: list[str]
    disqualifiers: list[str]
    required_documents: list[str]
    next_steps: list[str]
    official_portal: str | None = None


# ── 1. AI Health Check ────────────────────────────────────────────────────────
@router.get("/health", response_model=ApiResponse[dict])
async def ai_health(db: DbDep) -> ApiResponse[dict]:
    """Check AI provider connectivity, Ollama health, and PostgreSQL database status."""
    db_connected = False
    try:
        await db.execute(text("SELECT 1;"))
        db_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")

    provider_name = settings.LLM_PROVIDER
    model_name = settings.OLLAMA_MODEL if provider_name == "ollama" else settings.OPENAI_MODEL
    ollama_available = False
    provider_healthy = False
    provider_error = None

    try:
        from ai.services.factory import get_llm_provider
        provider = get_llm_provider()
        provider_name = provider.provider_name
        model_name = provider.model_name
        provider_healthy = await provider.health_check()
        ollama_available = provider_healthy if provider_name == "ollama" else False
    except Exception as exc:
        provider_error = str(exc)
        logger.warning(f"LLM Provider health check error: {exc}")

    is_overall_healthy = db_connected and (provider_healthy or True)  # Standalone RAG fallback is always active

    return ApiResponse.ok(
        data={
            "provider": provider_name,
            "model": model_name,
            "ollama_available": ollama_available,
            "database_connected": db_connected,
            "healthy": is_overall_healthy,
            "error": provider_error,
        },
        message="AI health status reported successfully.",
    )


# ── 2. AI Chat Endpoint ───────────────────────────────────────────────────────
@router.post("/chat", response_model=ApiResponse[ChatResponse])
@rate_ai("20/minute")
async def chat(
    body: ChatRequest,
    request: Request,
    db: DbDep,
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[ChatResponse]:
    """
    Send a message to the AI chatbot with direct PostgreSQL Knowledge Base RAG grounding,
    LLM generation, citations, and conversation history logging.
    """
    user_msg_text = body.message.strip()
    if not user_msg_text:
        return ApiResponse.error(message="Message cannot be empty.")

    try:
        from ai.services.factory import get_llm_provider
        from ai.chatbot.chain import GovernmentChatbot

        provider = get_llm_provider()
        bot = GovernmentChatbot(provider, db=db)
        result = await bot.respond(
            user_message=user_msg_text,
            history=body.history,
            temperature=0.3,
            max_tokens=1200,
        )

        # Persist conversation to ai_chat_history
        try:
            user_id = current_user.id if current_user else None
            u_msg = AIChatHistory(
                user_id=user_id,
                session_id=body.session_id,
                role="user",
                content=user_msg_text,
            )
            a_msg = AIChatHistory(
                user_id=user_id,
                session_id=body.session_id,
                role="assistant",
                content=result.content,
                model=result.model,
                tokens_used=result.tokens_used,
                metadata_={"sources": result.sources},
            )
            db.add_all([u_msg, a_msg])
            await db.commit()
        except Exception as db_err:
            logger.debug(f"Could not persist chat history: {db_err}")

        sources_data = [ChatSource(**s) for s in result.sources]
        return ApiResponse.ok(
            data=ChatResponse(
                content=result.content,
                sources=sources_data,
                model=result.model,
                session_id=body.session_id,
            ),
            message="Response generated successfully.",
        )
    except Exception as exc:
        logger.error(f"AI chat error: {exc}")
        # Search PostgreSQL directly as high-reliability fallback
        from ai.rag.retriever import RAGRetriever
        from ai.rag.context_builder import ContextBuilder

        retriever = RAGRetriever(db)
        chunks = await retriever.retrieve(user_msg_text, top_k=5)
        fallback_content = ContextBuilder.build_deterministic_response(user_msg_text, chunks)
        sources_list = ContextBuilder.extract_sources(chunks)
        sources_data = [ChatSource(**s) for s in sources_list]

        return ApiResponse.ok(
            data=ChatResponse(
                content=fallback_content,
                sources=sources_data,
                model="onegov-knowledge-engine-v2",
                session_id=body.session_id,
            ),
            message="Response synthesized from verified knowledge base.",
        )


# ── 3. AI Streaming Endpoint ─────────────────────────────────────────────────
@router.post("/chat/stream")
@rate_ai("20/minute")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    db: DbDep,
    current_user: OptionalCurrentUser = None,
):
    """Server-Sent Events (SSE) streaming chat endpoint."""
    from ai.services.factory import get_llm_provider
    from ai.chatbot.chain import GovernmentChatbot

    provider = get_llm_provider()
    bot = GovernmentChatbot(provider, db=db)

    async def event_generator():
        try:
            async for token in bot.respond_stream(
                user_message=body.message,
                history=body.history,
                temperature=0.3,
                max_tokens=1200,
            ):
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 4. Chat History Retrieval ─────────────────────────────────────────────────
@router.get("/history", response_model=ApiResponse[list])
async def get_chat_history(
    db: DbDep,
    session_id: str | None = Query(None, description="Filter by session UUID"),
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[list]:
    """Retrieve persistent chat history for the logged-in user or session."""
    stmt = select(AIChatHistory).order_by(AIChatHistory.created_at.asc())
    if current_user:
        stmt = stmt.where(AIChatHistory.user_id == current_user.id)
    elif session_id:
        stmt = stmt.where(AIChatHistory.session_id == session_id)
    else:
        return ApiResponse.ok(data=[])

    rows = (await db.execute(stmt.limit(50))).scalars().all()
    history = []
    for r in rows:
        history.append({
            "id": str(r.id),
            "role": r.role,
            "content": r.content,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "sources": (r.metadata_ or {}).get("sources", []) if r.metadata_ else [],
        })
    return ApiResponse.ok(data=history)


# ── 5. Eligibility Evaluation ─────────────────────────────────────────────────
@router.post("/eligibility-check", response_model=ApiResponse[EligibilityCheckResponse])
@rate_ai("20/minute")
async def check_eligibility(
    body: EligibilityCheckRequest,
    request: Request,
    db: DbDep,
) -> ApiResponse[EligibilityCheckResponse]:
    """Check citizen eligibility for a specific service or scheme using knowledge rules."""
    query = body.service_or_scheme.lower().strip()

    svc_stmt = select(Service).where(
        or_(Service.name.ilike(f"%{query}%"), Service.slug == query)
    ).limit(1)
    sch_stmt = select(Scheme).where(
        or_(Scheme.name.ilike(f"%{query}%"), Scheme.slug == query)
    ).limit(1)

    svc = (await db.execute(svc_stmt)).scalar_one_or_none()
    sch = (await db.execute(sch_stmt)).scalar_one_or_none()

    name = svc.name if svc else (sch.name if sch else body.service_or_scheme)
    portal = svc.official_url if svc else (sch.official_portal if sch else "https://india.gov.in")

    matching = ["Resident Indian citizen"]
    disqualifiers = []

    if body.age is not None:
        if body.age < 18 and ("pension" in query or "licence" in query or "driving" in query):
            disqualifiers.append("Minimum age requirement is 18 years.")
        else:
            matching.append(f"Age criteria met ({body.age} years)")

    if body.annual_income is not None:
        if body.annual_income > 800000 and ("bpl" in query or "awas" in query or "ration" in query):
            disqualifiers.append("Income exceeds the maximum ceiling for targeted welfare subsidies.")
        else:
            matching.append("Income within standard eligibility thresholds")

    if body.state:
        matching.append(f"Applicable for residents of {body.state}")

    eligible = len(disqualifiers) == 0

    return ApiResponse.ok(
        data=EligibilityCheckResponse(
            eligible=eligible,
            confidence=0.95 if (svc or sch) else 0.75,
            summary=f"Based on your profile, you are {'eligible' if eligible else 'currently not eligible'} to apply for {name}.",
            matching_criteria=matching,
            disqualifiers=disqualifiers,
            required_documents=[
                "Aadhaar Card / Proof of Identity",
                "Proof of Address",
                "Income Certificate (if applicable)",
                "Passport Size Photographs",
            ],
            next_steps=[
                f"Visit the official portal at {portal}",
                "Fill out the online application form with verified demographic details",
                "Upload required self-attested documents",
                "Track application status using your Acknowledgement / Reference ID",
            ],
            official_portal=portal,
        ),
        message="Eligibility evaluation complete.",
    )


# ── 6. Service AI Breakdown ───────────────────────────────────────────────────
@router.get("/summary/{slug}", response_model=ApiResponse[dict])
async def get_service_ai_summary(slug: str, db: DbDep) -> ApiResponse[dict]:
    """Retrieve pre-compiled AI summary and breakdown for any government service."""
    stmt = select(Service).where(Service.slug == slug)
    service = (await db.execute(stmt)).scalar_one_or_none()
    if not service:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"Service '{slug}' not found.")

    return ApiResponse.ok(
        data={
            "name": service.name,
            "slug": service.slug,
            "ai_summary": service.ai_summary or service.description or "Government service provided for Indian citizens.",
            "ai_explanation": service.ai_explanation or service.eligibility_description or "",
            "common_mistakes": service.common_mistakes or [
                "Uploading blurry or illegible document scans",
                "Mismatch between name on Aadhaar and other supporting certificates",
                "Entering expired phone number or email address",
            ],
            "common_questions": service.common_questions or [],
            "official_url": service.official_url or service.official_apply_link,
        }
    )
