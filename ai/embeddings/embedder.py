"""
OneGov AI — Real Embedding Service.

Generates genuine semantic embeddings using the configured provider
(Ollama nomic-embed-text by default; OpenAI text-embedding-3-small as an option).

This replaces the legacy deterministic hash-based "embeddings" which were
semantically meaningless. If the embedding provider is unavailable we do NOT
fall back to fake vectors — retrieval simply degrades to full-text search.
"""

import asyncio
import hashlib
from functools import lru_cache
from typing import Iterable

from loguru import logger

from ai.services.base_provider import LLMProvider


class EmbeddingUnavailableError(RuntimeError):
    """Raised when no embedding provider can generate embeddings."""


class EmbeddingService:
    """Provider-agnostic embedding service with dimension control and caching."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        dim: int | None = None,
        model: str | None = None,
    ) -> None:
        from app.core.config import settings

        self._provider = provider or self._default_provider()
        self.dim = dim or settings.EMBEDDING_DIM
        self.model = model or settings.EMBEDDING_MODEL
        self._cache: dict[str, list[float]] = {}

    @staticmethod
    def _default_provider() -> LLMProvider:
        from ai.services.factory import get_llm_provider
        return get_llm_provider()

    @staticmethod
    def _cache_key(text: str, model: str) -> str:
        return f"{model}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    async def embed_one(self, text: str) -> list[float]:
        """Embed a single text. Returns a normalised vector of ``self.dim``."""
        if not text or not text.strip():
            return [0.0] * self.dim

        cache_key = self._cache_key(text, self.model)
        if cache_key in self._cache:
            return self._cache[cache_key]

        response = await self._provider.embed(text)
        vector = self._normalize(response.embedding)
        self._cache[cache_key] = vector
        return vector

    async def embed_many(self, texts: Iterable[str], concurrency: int = 8) -> list[list[float]]:
        """Embed a batch of texts with bounded concurrency."""
        items = [t for t in texts if t and t.strip()]
        if not items:
            return []

        results: dict[int, list[float]] = {}
        sem = asyncio.Semaphore(concurrency)
        cache_key = self._cache_key

        async def _run(idx: int, text: str) -> None:
            key = cache_key(text, self.model)
            if key in self._cache:
                results[idx] = self._cache[key]
                return
            async with sem:
                resp = await self._provider.embed(text)
                vector = self._normalize(resp.embedding)
                self._cache[key] = vector
                results[idx] = vector

        await asyncio.gather(*(_run(i, t) for i, t in enumerate(items)))
        return [results[i] for i in range(len(items))]

    def _normalize(self, vector: list[float]) -> list[float]:
        vec = list(vector)
        if len(vec) != self.dim:
            if len(vec) > self.dim:
                vec = vec[: self.dim]
            else:
                vec = vec + [0.0] * (self.dim - len(vec))
        norm = sum(float(v) * float(v) for v in vec) ** 0.5
        if norm > 0:
            vec = [round(float(v) / norm, 6) for v in vec]
        return vec

    async def health_check(self) -> bool:
        try:
            await self._provider.embed("onegov health")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Embedding provider unavailable: {exc}")
            return False


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


async def force_embed_available() -> bool:
    """Compatibility helper used by health endpoints."""
    service = get_embedding_service()
    return await service.health_check()