"""
NVIDIA NIM Provider — NVIDIA Nemotron-3.5-Lightning-30b-A3B.
Optimised for high-throughput, structured digital public services assistance.
"""

import re
from typing import AsyncIterator
from loguru import logger

from ai.services.base_provider import ChatResponse, EmbeddingResponse, Message
from ai.services.resilience import measure_latency
from ai.services.usage import track_provider_usage


def strip_reasoning(content: str) -> str:
    if not content:
        return ""
    content_stripped = content.strip()
    
    # Strip explicit reasoning tags
    content_stripped = re.sub(r"<think>.*?</think>", "", content_stripped, flags=re.DOTALL)
    content_stripped = re.sub(r"<thought>.*?</thought>", "", content_stripped, flags=re.DOTALL)
    
    # Strip "Here's a thinking process:" or similar prefixes followed by lists
    lower_content = content_stripped.lower()
    if "thinking process" in lower_content or "thinking:" in lower_content or "thought process" in lower_content:
        match = re.search(r"\n(###\s+\w+|#+\s+\w+)", content_stripped)
        if match:
            content_stripped = content_stripped[match.start() + 1:].strip()
            
    return content_stripped


class NvidiaProvider:
    """LLM provider backed by the NVIDIA API (NIM OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model: str = "nvidia/nemotron-3.5-lightning-30b-a3b",
    ) -> None:
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120.0,
                max_retries=2,
            )
        except ImportError as e:
            raise ImportError("Install openai: pip install openai") from e
        self._model = model
        self._base_url = base_url

    @property
    def provider_name(self) -> str:
        return "nvidia"

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
                    extra_body={
                        "chat_template_kwargs": {
                            "enable_thinking": False
                        }
                    }
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
        
        # Strip reasoning content if present in the full content
        content = strip_reasoning(choice.message.content or "")
        return ChatResponse(
            content=content,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=usage.total_tokens if usage else input_tokens + output_tokens,
            latency_ms=round(latency_ms, 1),
            provider_used="nvidia",
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
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            }
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            
            # Specifically filter out internal reasoning/chain-of-thought to prevent exposure
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                continue
                
            delta_content = getattr(delta, "content", None)
            if delta_content:
                yield delta_content

    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Nvidia NIM doesn't host nomic-embed-text directly.
        Raises NotImplementedError to trigger fallback to default embedding service.
        """
        raise NotImplementedError("Embeddings not supported by NvidiaProvider. Use Ollama/OpenAI instead.")

    async def health_check(self) -> bool:
        try:
            # Retrieve model metadata to verify key and connection
            await self._client.models.retrieve(self._model)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"NVIDIA health check failed: {exc}")
            return False
