"""
Shared pytest fixtures for the entire test suite.
Provides: async DB session, Redis mock, authenticated HTTP client,
test user factory, and token generation utilities.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.base import Base
from app.models.role import Role
from app.models.user import User

# ── Async event loop ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory test database ────────────────────────────────────────────────────

from sqlalchemy.pool import NullPool

TEST_DB_URL = "postgresql+asyncpg://postgres@localhost:5433/onegov_test"

_test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
_TestSessionFactory = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once before the test session; drop them after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a test DB session that rolls back after each test.
    This keeps tests isolated without dropping/recreating tables.
    """
    async with _test_engine.connect() as conn:
        await conn.begin_nested()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


# ── Redis mock ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    """
    In-memory Redis mock using a dict so tests don't need a running Redis.
    Implements the subset of the Redis interface used by TokenService and OTPService.
    """
    store: dict[str, Any] = {}

    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(side_effect=lambda k: store.get(k))
    redis_mock.setex = AsyncMock(side_effect=lambda k, _ttl, v: store.update({k: v}))
    redis_mock.set = AsyncMock(side_effect=lambda k, v, **kw: store.update({k: v}))
    redis_mock.delete = AsyncMock(side_effect=lambda *keys: [store.pop(k, None) for k in keys])
    redis_mock.exists = AsyncMock(side_effect=lambda *keys: sum(1 for k in keys if k in store))
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.incr = AsyncMock(side_effect=lambda k: store.update({k: store.get(k, 0) + 1}) or store[k])

    async def scan_iter_mock(pattern: str):
        prefix = pattern.replace("*", "")
        for key in list(store.keys()):
            if key.startswith(prefix):
                yield key

    redis_mock.scan_iter = scan_iter_mock
    redis_mock.ping = AsyncMock(return_value=True)

    return redis_mock


# ── FastAPI test app ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def app(db_session: AsyncSession, mock_redis: AsyncMock) -> FastAPI:
    """Test FastAPI app with DB and Redis overridden."""
    application = create_app()

    application.dependency_overrides[get_db] = lambda: db_session
    application.dependency_overrides[get_redis] = lambda: mock_redis

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ── Test data factories ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def user_role(db_session: AsyncSession) -> Role:
    role = Role(name="user", description="Standard user", is_system=True)
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Role:
    role = Role(name="admin", description="Administrator", is_system=True)
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, user_role: Role) -> User:
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=hash_password("Test@1234!"),
        is_active=True,
        is_email_verified=True,
    )
    user.roles.append(user_role)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_role: Role) -> User:
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        password_hash=hash_password("Admin@1234!"),
        is_active=True,
        is_email_verified=True,
    )
    user.roles.append(admin_role)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# ── Auth helpers ───────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers for the test user."""
    token, _ = create_access_token(subject=str(test_user.id), role="user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token, _ = create_access_token(subject=str(admin_user.id), role="admin")
    return {"Authorization": f"Bearer {token}"}
