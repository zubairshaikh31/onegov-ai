"""Health check endpoints — used by Docker, load balancers, and monitoring."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    services: dict[str, str]


@router.get("", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """
    Returns 200 if the API is running.
    Also reports the status of downstream services (DB, Redis).
    Used by Docker HEALTHCHECK and uptime monitoring.
    """
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    services = {
        "database": "healthy" if db_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
    }

    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"

    return HealthStatus(
        status=overall,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        services=services,
    )


@router.get("/ping", summary="Ping")
async def ping() -> dict[str, str]:
    """Simple liveness probe — no DB/Redis calls. Used by Nginx upstreams."""
    return {"ping": "pong"}
