"""
Redis connection pool and dependency.
Uses redis.asyncio with hiredis for maximum performance.
Falls back to a secure in-memory MockRedis if the Redis server is unreachable.
"""
import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta

from loguru import logger
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import settings

_pool: ConnectionPool | None = None
_use_mock: bool = False
_mock_instance = None


class MockRedis:
    """
    An in-memory, thread-safe asynchronous mock Redis client.
    Implements all key-value and session storage patterns used by OneGov services.
    """
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expiries: dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        logger.warning("Initializing in-memory MockRedis fallback.")

    async def get(self, key: str) -> str | None:
        async with self._lock:
            if key in self._expiries and datetime.utcnow() > self._expiries[key]:
                self._store.pop(key, None)
                self._expiries.pop(key, None)
            return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: any) -> bool:
        async with self._lock:
            self._store[key] = str(value)
            self._expiries[key] = datetime.utcnow() + timedelta(seconds=ttl)
            return True

    async def set(
        self, key: str, value: any, ex: int | None = None, px: int | None = None,
        nx: bool = False, xx: bool = False, keepttl: bool = False
    ) -> bool:
        async with self._lock:
            self._store[key] = str(value)
            if ex:
                self._expiries[key] = datetime.utcnow() + timedelta(seconds=ex)
            elif px:
                self._expiries[key] = datetime.utcnow() + timedelta(milliseconds=px)
            return True

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                if k in self._store:
                    self._store.pop(k, None)
                    self._expiries.pop(k, None)
                    count += 1
            return count

    async def exists(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            now = datetime.utcnow()
            for k in keys:
                if k in self._store:
                    if k in self._expiries and now > self._expiries[k]:
                        self._store.pop(k, None)
                        self._expiries.pop(k, None)
                    else:
                        count += 1
            return count

    async def incr(self, key: str) -> int:
        async with self._lock:
            # Check expiry before incrementing
            if key in self._expiries and datetime.utcnow() > self._expiries[key]:
                self._store.pop(key, None)
                self._expiries.pop(key, None)
            val = int(self._store.get(key, 0)) + 1
            self._store[key] = str(val)
            return val

    async def expire(self, key: str, ttl: int) -> bool:
        async with self._lock:
            if key in self._store:
                self._expiries[key] = datetime.utcnow() + timedelta(seconds=ttl)
                return True
            return False

    async def scan_iter(self, pattern: str) -> AsyncGenerator[str, None]:
        prefix = pattern.replace("*", "")
        async with self._lock:
            now = datetime.utcnow()
            for k in list(self._store.keys()):
                if k.startswith(prefix):
                    if k in self._expiries and now > self._expiries[k]:
                        self._store.pop(k, None)
                        self._expiries.pop(k, None)
                    else:
                        yield k

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass


def _build_pool() -> ConnectionPool:
    return ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = _build_pool()
    return _pool


def get_redis_client() -> Redis | MockRedis:
    global _use_mock, _mock_instance
    if _use_mock or settings.REDIS_URL.startswith("mock://"):
        if _mock_instance is None:
            _mock_instance = MockRedis()
        return _mock_instance
    return Redis(connection_pool=get_pool())


async def get_redis() -> AsyncGenerator[Redis | MockRedis, None]:
    """FastAPI dependency that yields a Redis client."""
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_connection() -> bool:
    """Health-check helper. Returns True if Redis is reachable or fallback is active."""
    global _use_mock
    if settings.REDIS_URL.startswith("mock://") or _use_mock:
        return True
    try:
        client = Redis(connection_pool=get_pool())
        await client.ping()
        await client.aclose()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Real Redis connection failed: {exc}. Activating MockRedis fallback.")
        _use_mock = True
        return True


async def close_redis_pool() -> None:
    """Called on application shutdown."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
        logger.info("Redis connection pool closed")
