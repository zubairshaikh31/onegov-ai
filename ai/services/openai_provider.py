"""
OpenAI provider — GPT-4o-mini by default.
Drop-in replacement for OllamaProvider.
Activate by setting LLM_PROVIDER=openai in .env.
"""

from typing import AsyncIterator

from loguru import logger

from ai.services.base_provider import ChatResponse, EmbeddingResponse, Message
from ai.services.resilience import measure_latency
from ai.services.usage import track_provider_usage


class OpenAIProvider:
    """LLM provider backed by the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=api_key,
                timeout=120.0,
                max_retries=2,
            )
        except ImportError as e:
            raise ImportError("Install openai: pip install openai") from e
        self._model = model
        self._embedding_model = embedding_model

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ChatResponse:
        try:
            async def _call():
                return await self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[list-item]
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            (response, latency_ms) = await measure_latency(_call)
        except Exception:  # noqa: BLE001
            track_provider_usage("chat", error=True)
            raise
        choice = response.choices[0]
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        track_provider_usage("chat", input_tokens, output_tokens, latency_ms)
        return ChatResponse(
            content=choice.message.content or "",
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=response.usage.total_tokens if usage else input_tokens + output_tokens,
            latency_ms=round(latency_ms, 1),
            provider_used="openai",
        )

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[list-item]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, text: str) -> EmbeddingResponse:
        try:
            async def _call():
                return await self._client.embeddings.create(
                    model=self._embedding_model,
                    input=text,
                )

            (response, latency_ms) = await measure_latency(_call)
        except Exception:  # noqa: BLE001
            track_provider_usage("embed", error=True)
            raise
        embedding_data = response.data[0]
        tokens = response.usage.prompt_tokens
        track_provider_usage("embed", tokens, 0, latency_ms)
        return EmbeddingResponse(
            embedding=embedding_data.embedding,
            model=self._embedding_model,
            input_tokens=tokens,
            latency_ms=round(latency_ms, 1),
            provider_used="openai",
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.retrieve(self._model)
            return True
        except Exception:  # noqa: BLE001
            return False
