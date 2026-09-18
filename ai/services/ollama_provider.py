"""
Ollama provider — connects to a local Ollama server.
Zero API cost. Runs llama3.2 (or any other Ollama model) locally.
Requires: `docker compose up ollama` then `docker exec onegov_ollama ollama pull llama3.2`
"""

import json
from typing import AsyncIterator

import httpx
from loguru import logger

from ai.services.base_provider import ChatResponse, EmbeddingResponse, Message
from ai.services.resilience import call_with_retry, measure_latency
from ai.services.usage import track_provider_usage


class OllamaProvider:
    """LLM provider backed by a local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "llama3.2",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._embedding_model = embedding_model
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=15.0))

    @property
    def provider_name(self) -> str:
        return "ollama"

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
        """Non-streaming chat completion via Ollama /api/chat (retried)."""
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async def _call():
            response = await self._client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response

        try:
            (response, latency_ms) = await measure_latency(
                call_with_retry, lambda: _call()
            )
            data = response.json()
            content = data["message"]["content"]
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)
            track_provider_usage("chat", prompt_eval_count, eval_count, latency_ms)
            return ChatResponse(
                content=content,
                model=self._model,
                input_tokens=prompt_eval_count,
                output_tokens=eval_count,
                total_tokens=prompt_eval_count + eval_count,
                latency_ms=round(latency_ms, 1),
                provider_used="ollama",
            )
        except httpx.HTTPStatusError as e:
            track_provider_usage("chat", error=True)
            logger.error(f"Ollama API error: {e.response.status_code} — {e.response.text}")
            raise
        except httpx.ConnectError:
            track_provider_usage("chat", error=True)
            logger.error(f"Cannot connect to Ollama at {self._base_url}")
            raise

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Streaming chat — yields text tokens as they arrive."""
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            async with self._client.stream(
                "POST", f"{self._base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            track_provider_usage(
                                "chat",
                                chunk.get("prompt_eval_count", 0),
                                chunk.get("eval_count", 0),
                            )
                            break
                    except json.JSONDecodeError:
                        continue
        except httpx.HTTPStatusError as e:
            track_provider_usage("chat", error=True)
            logger.error(f"Ollama stream error: {e.response.status_code} — {e.response.text}")
            raise

    # ── Embeddings ────────────────────────────────────────────────────────────

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using Ollama's /api/embed endpoint (retried)."""
        payload = {
            "model": self._embedding_model,
            "input": text,
        }

        async def _call():
            response = await self._client.post(f"{self._base_url}/api/embed", json=payload)
            response.raise_for_status()
            return response

        try:
            (response, latency_ms) = await measure_latency(
                call_with_retry, lambda: _call()
            )
            data = response.json()
            embeddings = data.get("embeddings", [[]])[0]
            tokens = data.get("prompt_eval_count", 0)
            track_provider_usage("embed", tokens, 0, latency_ms)
            return EmbeddingResponse(
                embedding=embeddings,
                model=self._embedding_model,
                input_tokens=tokens,
                latency_ms=round(latency_ms, 1),
                provider_used="ollama",
            )
        except httpx.HTTPStatusError as e:
            track_provider_usage("embed", error=True)
            logger.error(f"Ollama embed error: {e.response.text}")
            raise

    # ── Health ────────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(f"{self._base_url}/api/version", timeout=5.0)
            return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    async def pull_model(self, model_name: str | None = None) -> None:
        """Pull a model if it's not already available. Call this at startup."""
        name = model_name or self._model
        logger.info(f"Pulling Ollama model: {name}")
        payload = {"name": name, "stream": False}
        try:
            response = await self._client.post(
                f"{self._base_url}/api/pull", json=payload, timeout=600.0
            )
            response.raise_for_status()
            logger.info(f"Model {name} ready")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Could not pull model {name}: {exc}")
