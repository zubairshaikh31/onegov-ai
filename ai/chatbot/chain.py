"""
OneGov AI Chatbot — RAG-powered, context-aware government services assistant.
Integrates pgvector similarity retrieval with LLM generation.
"""

from typing import Any, AsyncIterator
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.rag.pipeline import RAGPipeline, RAGResult
from ai.services.base_provider import ChatResponse, LLMProvider


class GovernmentChatbot:
    """
    RAG-powered conversational assistant.
    Retrieves top verified government knowledge chunks before generating answers.
    """

    def __init__(self, provider: LLMProvider, db: AsyncSession | None = None) -> None:
        self._provider = provider
        self._rag = RAGPipeline(provider, db=db)

    async def respond(
        self,
        user_message: str,
        history: list[dict],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> RAGResult:
        """Generate RAG-grounded response with verified sources and citations."""
        logger.debug(f"RAG Chatbot query: {user_message[:60]}")
        return await self._rag.answer(
            query=user_message,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def respond_stream(
        self,
        user_message: str,
        history: list[dict],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> AsyncIterator[str]:
        """Streaming token-by-token generator for real-time SSE output."""
        async for token in self._rag.stream_answer(
            query=user_message,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield token

    async def health_check(self) -> bool:
        return await self._provider.health_check()
