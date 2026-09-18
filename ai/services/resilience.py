"""
OneGov AI — Provider Resilience Helpers.

Retries with exponential backoff on transient failures so the chatbot survives
local model restarts (Ollama) and provider blips (5xx / 429 / timeouts).
"""

import asyncio
import time
from typing import Awaitable, Callable, TypeVar

import httpx

T = TypeVar("T")

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


async def call_with_retry(
    fn: Callable[..., Awaitable[T]],
    *args,
    retries: int | None = None,
    timeout_override: float | None = None,
    **kwargs,
) -> T:
    """
    Execute an async call, retrying transient failures with exponential backoff.

    Retried when: ConnectError, NetworkError, TimeoutException, or an HTTP status
    in RETRYABLE_STATUS. Non-transient errors propagate immediately.
    """
    from app.core.config import settings

    attempts = (settings.LLM_MAX_RETRIES if retries is None else retries) + 1
    last_exc: Exception | None = None

    for attempt in range(attempts):
        try:
            return await fn(*args, **kwargs, timeout=timeout_override) if timeout_override else await fn(*args, **kwargs)
        except (httpx.ConnectError, httpx.NetworkError, httpx.TimeoutException) as exc:
            last_exc = exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS:
                raise
            last_exc = exc
        except Exception as exc:  # noqa: BLE001
            # Non-transient — propagate immediately rather than mask real bugs.
            raise
        if attempt < attempts - 1:
            await asyncio.sleep(0.25 * (2**attempt))

    assert last_exc is not None
    raise last_exc


async def measure_latency(fn: Callable[..., Awaitable[T]], *args, **kwargs) -> tuple[T, float]:
    """Run an async call and return (result, latency_ms)."""
    start = time.perf_counter()
    result = await fn(*args, **kwargs)
    return result, (time.perf_counter() - start) * 1000.0