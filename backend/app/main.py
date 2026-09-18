"""FastAPI application factory."""
import sys
from pathlib import Path
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

for p in [str(PROJECT_ROOT), str(BACKEND_DIR), "/", "/app"]:
    if p not in sys.path:
        sys.path.insert(0, p)


from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import OneGovError
from app.core.logging import setup_logging
from app.core.redis import close_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    await _seed_default_roles()
    yield
    logger.info("Shutting down...")
    await close_redis_pool()
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="OneGov AI — Intelligent Public Access to Digital Government Services.",
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rate limiter ───────────────────────────────────────────────────────────
    from app.middleware.rate_limit import limiter_storage_uri

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=limiter_storage_uri(),
        default_limits=["200/minute"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Exception handlers ─────────────────────────────────────────────────────
    @app.exception_handler(OneGovError)
    async def onegov_handler(request: Request, exc: OneGovError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "errors": [{"code": exc.error_code, "message": exc.message}],
            },
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled: {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error.", "data": None, "errors": None},
        )

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


async def _seed_default_roles() -> None:
    from sqlalchemy import select
    from app.core.database import AsyncSessionFactory
    from app.models.role import Role
    try:
        async with AsyncSessionFactory() as session:
            for name, desc in [
                ("admin", "Platform administrator"),
                ("user", "Standard citizen user"),
                ("moderator", "Content moderator"),
            ]:
                if not (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none():
                    session.add(Role(name=name, description=desc, is_system=True))
                    logger.info(f"Created role: {name}")
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not seed roles (tables may not exist yet): {exc}")


app = create_app()
