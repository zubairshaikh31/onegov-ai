"""
LLM provider factory.
The single place that knows which concrete provider to instantiate.
All other modules call get_llm_provider() and work against the protocol.

Supports an optional fallback provider (LLM_FALLBACK_PROVIDER) so the chatbot
responds even when the primary provider (e.g. local Ollama) is down.
"""

from functools import lru_cache
from typing import AsyncIterator

from loguru import logger

from ai.services.base_provider import LLMProvider


class ProviderWithFallback:
    """
    Transparent primary→fallback wrapper. Application code keeps working
    against the LLMProvider protocol and never sees provider failure modes.
    """

    def __init__(self, primary: LLMProvider, fallback: LLMProvider | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    @property
    def provider_name(self) -> str:
        return self._primary.provider_name

    @property
    def model_name(self) -> str:
        return self._primary.model_name

    async def chat(self, messages, **kwargs):
        try:
            return await self._primary.chat(messages, **kwargs)
        except Exception as exc:  # noqa: BLE001
            if self._fallback is None:
                raise
            logger.warning(f"Primary provider failed ({exc}); falling back to {self._fallback.provider_name}")
            from dataclasses import replace
            resp = await self._fallback.chat(messages, **kwargs)
            return replace(resp, provider_used=f"{self._fallback.provider_name} (fallback)")

    async def chat_stream(self, messages, **kwargs) -> AsyncIterator[str]:
        error = None
        try:
            async for token in self._primary.chat_stream(messages, **kwargs):
                yield token
            return
        except Exception as exc:  # noqa: BLE001
            error = exc
        if self._fallback is None:
            raise error  # type: ignore[misc]
        logger.warning(f"Primary stream failed ({error}); falling back to {self._fallback.provider_name}")
        async for token in self._fallback.chat_stream(messages, **kwargs):
            yield token

    async def embed(self, text: str):
        try:
            return await self._primary.embed(text)
        except Exception as exc:  # noqa: BLE001
            if self._fallback is None:
                raise
            logger.warning(f"Primary embed failed ({exc}); falling back to {self._fallback.provider_name}")
            from dataclasses import replace
            resp = await self._fallback.embed(text)
            return replace(resp, provider_used=f"{self._fallback.provider_name} (fallback)")

    async def health_check(self) -> bool:
        return await self._primary.health_check()


def _build_provider(name: str, settings) -> LLMProvider:
    if name == "ollama":
        from ai.services.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            embedding_model=settings.EMBEDDING_MODEL,
        )

    if name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set when provider is 'openai'")
        from ai.services.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )

    if name == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set when provider is 'gemini'")
        from ai.services.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)

    if name == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY must be set when provider is 'groq'")
        from ai.services.groq_provider import GroqProvider
        return GroqProvider(api_key=settings.GROQ_API_KEY)

    if name == "nvidia":
        if not settings.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY must be set when provider is 'nvidia'")
        from ai.services.nvidia_provider import NvidiaProvider
        return NvidiaProvider(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
            model=settings.NVIDIA_MODEL,
        )

    raise ValueError(
        f"Unknown provider '{name}'. Valid options: ollama, openai, gemini, groq, claude, nvidia"
    )


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """
    Read LLM_PROVIDER / LLM_FALLBACK_PROVIDER from environment and return the
    corresponding provider (wrapped with a fallback when configured).
    Cached with lru_cache so the provider is a singleton (one HTTP client).

    To switch providers at runtime (e.g. in tests), call get_llm_provider.cache_clear()
    before calling get_llm_provider() again.
    """
    # Import here to avoid circular imports and unnecessary dependency loading
    from app.core.config import settings

    provider_name = settings.LLM_PROVIDER
    logger.info(f"Initialising LLM provider: {provider_name}")
    primary = _build_provider(provider_name, settings)

    fallback_name = settings.LLM_FALLBACK_PROVIDER
    fallback = None
    if fallback_name and fallback_name != "none" and fallback_name != provider_name:
        logger.info(f"Fallback LLM provider: {fallback_name}")
        try:
            fallback = _build_provider(fallback_name, settings)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Fallback provider '{fallback_name}' unavailable: {exc}")

    return ProviderWithFallback(primary=primary, fallback=fallback)


def get_llm_provider_for_testing(provider: LLMProvider) -> None:
    """
    Override the provider for testing without restarting the process.
    Usage in conftest.py:
        monkeypatch.setattr("ai.services.factory.get_llm_provider", lambda: mock_provider)
    """
    get_llm_provider.cache_clear()