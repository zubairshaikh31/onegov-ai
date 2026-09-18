"""
LLM Provider abstraction layer.

This is the architectural centrepiece of the AI module.
The Protocol defines the contract; concrete providers implement it.
Application code depends ONLY on this interface — never on a specific SDK.

Switching from Ollama to OpenAI requires changing one environment variable,
not touching any business logic.

Supported providers (Phase 1 → Phase 4):
  - ollama   → OllamaProvider   (default, free, local)
  - openai   → OpenAIProvider   (GPT-4o-mini)
  - gemini   → GeminiProvider   (Gemini 1.5 Flash)
  - groq     → GroqProvider     (Llama/Mixtral via Groq API)
  - claude   → ClaudeProvider   (Anthropic Claude)
"""

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, runtime_checkable


@dataclass
class Message:
    """A single chat message."""
    role: str      # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from a chat completion."""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    provider_used: str = ""


@dataclass
class EmbeddingResponse:
    """Response from an embedding request."""
    embedding: list[float]
    model: str
    input_tokens: int = 0
    latency_ms: float = 0.0
    provider_used: str = ""


@runtime_checkable
class LLMProvider(Protocol):
    """
    Contract that every LLM provider must satisfy.
    All methods are async to support concurrent request handling.
    """

    @property
    def provider_name(self) -> str:
        """Human-readable name, e.g. 'ollama', 'openai'."""
        ...

    @property
    def model_name(self) -> str:
        """Model identifier, e.g. 'llama3.2', 'gpt-4o-mini'."""
        ...

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ChatResponse:
        """
        Send a list of chat messages and return a complete response.
        Use this for non-streaming interactions (eligibility check, summary, etc.).
        """
        ...

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """
        Send chat messages and yield response tokens as they arrive.
        Use this for the chatbot UI so users see words appearing in real time.
        """
        ...

    async def embed(self, text: str) -> EmbeddingResponse:
        """
        Generate a vector embedding for a piece of text.
        Used for semantic search and RAG retrieval.
        """
        ...

    async def health_check(self) -> bool:
        """Return True if the provider is reachable and responding."""
        ...
