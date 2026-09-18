"""
Rate limiting middleware.
Uses slowapi backed by Redis for distributed rate limiting across instances.

Storage strategy (fail-safe):
  - Production: Redis (distributed limits across instances).
  - Development/staging: in-memory storage so a Redis outage NEVER takes the
    API down. Rate limits must not be a single point of failure for
    authentication, search, or AI endpoints.

Limits are defined per-endpoint category:
  - Public endpoints:    200 req/min per IP
  - Auth endpoints:       10 req/min per IP  (anti brute-force)
  - AI endpoints:         20 req/min per user (LLM cost control)
  - Search endpoints:     60 req/min per IP

The key_func determines who is rate-limited.
Unauthenticated requests use IP; authenticated use user_id.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def limiter_storage_uri() -> str:
    """Redis in production; in-memory otherwise (never let the limiter break the API)."""
    if settings.is_production:
        return settings.REDIS_URL
    return "memory://"


def _user_or_ip_key(request: Request) -> str:
    """
    Rate-limit key: user ID for authenticated requests, IP for anonymous.
    This ensures one heavy user can't exhaust limits for everyone on a shared IP
    (e.g. corporate NAT, university WiFi).
    """
    # Check if the request has already been authenticated by the dependency layer
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)


# ── Limiter instances ──────────────────────────────────────────────────────────

# Default limiter — used for general API endpoints
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=limiter_storage_uri(),
    default_limits=["200/minute"],
    strategy="fixed-window",        # predictable reset behaviour
)

# Auth limiter — stricter, IP-based (user may not be authenticated yet)
auth_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=limiter_storage_uri(),
    default_limits=["10/minute"],
)

# AI limiter — per user to control LLM token spend
ai_limiter = Limiter(
    key_func=_user_or_ip_key,
    storage_uri=limiter_storage_uri(),
    default_limits=["20/minute"],
)

# Search limiter
search_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=limiter_storage_uri(),
    default_limits=["60/minute"],
)


# ── Decorator shortcuts ────────────────────────────────────────────────────────
# Import these in endpoint files for cleaner decorator syntax:
#   from app.middleware.rate_limit import rate_auth, rate_ai
#
# Usage:
#   @router.post("/login")
#   @rate_auth("5/minute")
#   async def login(...): ...

def rate_auth(limit: str = "10/minute"):
    return auth_limiter.limit(limit)


def rate_ai(limit: str = "20/minute"):
    return ai_limiter.limit(limit)


def rate_search(limit: str = "60/minute"):
    return search_limiter.limit(limit)


def rate_public(limit: str = "200/minute"):
    return limiter.limit(limit)
