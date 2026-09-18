"""
OneGov AI — Provider Usage Tracker.

A lightweight in-memory accumulator for LLM/embedding usage: calls, tokens,
latency and estimated cost. Exposed via the admin endpoints. Values are
per-process; production monitoring should also emit to an external system.

No secrets are logged anywhere in this module.
"""

import time
from threading import Lock
from typing import Any


class UsageTracker:
    """Thread-safe per-process usage accumulator."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.provider: str = ""
        self.model: str = ""
        self.calls: int = 0
        self.embed_calls: int = 0
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.total_latency_ms: float = 0.0
        self.errors: int = 0
        self.started_at: float = time.monotonic()
        self._input_price_per_1m: float = 0.0
        self._output_price_per_1m: float = 0.0

    def configure(
        self,
        provider: str = "",
        model: str = "",
        input_price_per_1m: float = 0.0,
        output_price_per_1m: float = 0.0,
    ) -> None:
        with self._lock:
            self.provider = provider
            self.model = model
            self._input_price_per_1m = input_price_per_1m
            self._output_price_per_1m = output_price_per_1m

    def track(
        self,
        kind: str = "chat",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        error: bool = False,
    ) -> None:
        with self._lock:
            self.calls += 1
            if kind == "embed":
                self.embed_calls += 1
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.total_latency_ms += latency_ms
            if error:
                self.errors += 1

    @property
    def est_cost_usd(self) -> float:
        with self._lock:
            return (
                self.input_tokens / 1_000_000 * self._input_price_per_1m
                + self.output_tokens / 1_000_000 * self._output_price_per_1m
            )

    @property
    def avg_latency_ms(self) -> float:
        with self._lock:
            if self.calls == 0:
                return 0.0
            return round(self.total_latency_ms / self.calls, 1)

    def uptime_seconds(self) -> int:
        return int(time.monotonic() - self.started_at)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "provider": self.provider,
                "model": self.model,
                "calls": self.calls,
                "embed_calls": self.embed_calls,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
                "errors": self.errors,
                "error_rate": round(self.errors / max(1, self.calls), 4),
                "avg_latency_ms": self.avg_latency_ms,
                "est_cost_usd": round(self.est_cost_usd, 6),
                "uptime_seconds": self.uptime_seconds(),
            }

    def reset(self) -> None:
        with self._lock:
            self.calls = 0
            self.embed_calls = 0
            self.input_tokens = 0
            self.output_tokens = 0
            self.total_latency_ms = 0.0
            self.errors = 0
            self.started_at = time.monotonic()


_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    return _tracker


def track_provider_usage(
    kind: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: float = 0.0,
    error: bool = False,
) -> None:
    get_usage_tracker().track(kind, input_tokens, output_tokens, latency_ms, error)