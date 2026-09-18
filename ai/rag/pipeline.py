"""
OneGov AI — Full RAG Pipeline
Orchestrates Retrieval, Context Building, and LLM Generation.
"""

import re
from dataclasses import dataclass
from typing import Any, AsyncIterator
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.rag.context_builder import ContextBuilder
from ai.rag.retriever import RAGRetriever, RetrievedChunk
from ai.services.base_provider import LLMProvider, Message


@dataclass
class RAGResult:
    content: str
    sources: list[dict[str, Any]]
    model: str
    tokens_used: int
    retrieved_chunks: list[RetrievedChunk]


def detect_state(query: str) -> str | None:
    states_uts = [
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
        "himachal pradesh", "jharkhand", "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
        "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
        "tripura", "uttar pradesh", "uttarakhand", "west bengal", "delhi", "jammu & kashmir", "jammu and kashmir",
        "puducherry", "chandigarh", "ladakh", "lakshadweep"
    ]
    query_lower = query.lower()
    for state in states_uts:
        if re.search(rf"\b{re.escape(state)}\b", query_lower):
            if state in ("jammu & kashmir", "jammu and kashmir"):
                return "Jammu & Kashmir"
            return state.title()
    return None


def classify_query(query: str, chunks: list[RetrievedChunk]) -> str:
    query_lower = query.lower().strip()
    
    # Rule-based checks for general chitchat or generic programming/science/writing queries
    general_keywords = {
        "python", "javascript", "java", "c++", "programming", "code", "coding", "algorithm", "recursion",
        "machine learning", "neural network", "artificial intelligence", "database", "sql join", "html", "css",
        "photosynthesis", "gravity", "physics", "chemistry", "biology", "science", "math", "calculate", "fibonacci",
        "write a letter", "write an email", "professional email", "interview questions",
        "hello", "hi", "hey", "how are you", "who are you", "what is your name", "thank you", "thanks", "joke",
        "explain", "what is", "define"
    }
    
    is_generic = False
    for kw in general_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", query_lower):
            is_generic = True
            break

    gov_keywords = {
        "apply", "license", "licence", "aadhaar", "passport", "scheme", "welfare", "caste", "pension", 
        "ration", "pan card", "birth", "death", "voter", "kisan", "ayushman", "government", "gov", "official",
        "portal", "yojana", "documents", "eligible", "eligibility", "fees", "processing time", "helpline", "ministry",
        "gst", "tax"
    }
    has_gov = any(re.search(rf"\b{re.escape(kw)}\b", query_lower) for kw in gov_keywords)
    
    has_strong_chunk = len(chunks) > 0 and chunks[0].confidence >= 0.35
    
    if is_generic and not has_gov:
        return "GENERAL"
        
    if has_gov and is_generic:
        return "MIXED"
        
    if not has_gov and not has_strong_chunk:
        return "GENERAL"
        
    if "eligible" in query_lower or "eligibility" in query_lower or "qualify" in query_lower or "who can" in query_lower:
        return "ELIGIBILITY"
    if "document" in query_lower or "required paper" in query_lower or "checklist" in query_lower:
        return "DOCUMENTS"
    if "apply" in query_lower or "process" in query_lower or "how to" in query_lower or "step" in query_lower:
        return "APPLICATION_PROCESS"
    if "faq" in query_lower or "question" in query_lower:
        return "GOVERNMENT_FAQ"
        
    if has_strong_chunk:
        top_type = chunks[0].entity_type
        if top_type == "scheme":
            return "GOVERNMENT_SCHEME"
        elif top_type == "faq":
            return "GOVERNMENT_FAQ"
        else:
            return "GOVERNMENT_SERVICE"
            
    return "GENERAL"


def get_system_prompt(classification: str, state_name: str | None, has_strong_context: bool) -> str:
    base_instructions = """You are OneGov AI — the intelligent digital government assistant for Indian citizens.
[IMPORTANT] Under no circumstances should you output any thinking process, internal analysis, notes, reasoning process, or internal monologue. Output ONLY the final answer in the format specified below.
"""

    if classification == "GENERAL":
        return base_instructions + """
You are acting as a general AI assistant. Answer the user's query directly and cleanly using your general knowledge.
- Do NOT use the government service/scheme template.
- Do NOT refuse to answer.
- Answer naturally, conversationally, and concisely.
- Write in a clean, professional markdown format.
"""

    state_context = f"\nNote: The user is applying in/asking about the state of: {state_name}." if state_name else ""
    
    gov_prompt = base_instructions + f"""
Your job is to provide accurate, step-by-step, actionable guidance on Indian government services and welfare schemes.{state_context}

CRITICAL INSTRUCTIONS:
1. When answering, base your response on the provided verified database context if available.
2. If the database context is empty or does not contain verified records for the requested service/scheme, do NOT refuse to answer. Instead, provide a helpful general overview of the typical process in India based on your general knowledge, and explicitly add a warning/notice advising the user to verify the exact details and requirements on the official government portal.
3. Every answer concerning a service or scheme should try to cover the following sections when the information is available (do not display empty sections. If the information is not available, omit the section instead of saying "Not available"):
   - ### Short answer (a concise overview)
   - ### Eligibility (who qualifies)
   - ### Required documents (checklist)
   - ### How to apply (numbered steps)
   - ### Fee & Processing time (only if verified in context or general estimates clearly marked as general)
   - ### Official portal (link to the official portal if verified)
4. Do NOT hallucinate specific fees, helpline numbers, or portal URLs. If they are not in the verified context, state that they must be verified on the official portal.
5. Write in crisp, professional, easy-to-read startup formatting (Stripe/Linear style with clean bullet points, bold headers, and numbered steps).
6. If the user is asking about highly state-dependent services (like caste certificate, ration card, income certificate, or domicile) and has not specified their state in the query or conversation history, ask them concisely: "Which state or UT are you applying in?" to provide accurate guidance.
7. If the citizen asks in Hindi, answer in Hindi. If in Marathi, answer in Marathi. Otherwise use clear English.
"""
    return gov_prompt


class RAGPipeline:
    """End-to-end RAG orchestrator for OneGov AI."""

    def __init__(self, provider: LLMProvider, db: AsyncSession | None = None) -> None:
        self.provider = provider
        self.retriever = RAGRetriever(db)

    async def answer(
        self,
        query: str,
        history: list[dict] | None = None,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> RAGResult:
        """Run full RAG pipeline: Retrieve -> Build Context -> Generate Answer."""
        history = history or []

        # 1. Detect state from current query or history context
        state_name = detect_state(query)
        if not state_name:
            for h in reversed(history[-6:]):
                prev_state = detect_state(h.get("content", ""))
                if prev_state:
                    state_name = prev_state
                    break

        # 2. Retrieve top chunks
        chunks = await self.retriever.retrieve(query, top_k=5)
        
        # 3. Classify query
        classification = classify_query(query, chunks)
        logger.info(f"Chatbot query classification: {classification} (State: {state_name})")

        # 4. Build Context and extract sources
        has_strong_context = len(chunks) > 0 and chunks[0].confidence >= 0.35
        
        if classification == "GENERAL":
            context_str = "No specific government knowledge base context is required for this general query."
            sources = []
        else:
            if not has_strong_context and not any(detect_state(c.title) or detect_state(c.chunk_text) for c in chunks):
                context_str = "No verified database records matched this query. Provide general guidance based on official Indian government processes, and instruct the user to verify all details on the official portal."
                sources = []
            else:
                context_str = ContextBuilder.build_context(chunks)
                sources = ContextBuilder.extract_sources(chunks)

        system_prompt = get_system_prompt(classification, state_name, has_strong_context)

        # 5. Build LLM Messages
        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="system", content=context_str),
        ]

        # Add recent conversation history (last 6 turns)
        for h in history[-12:]:
            messages.append(Message(role=h.get("role", "user"), content=h.get("content", "")))

        # Append final negative constraint to query to avoid Nemotron/Deepseek reasoning leaks
        user_prompt = query
        if classification != "GENERAL":
            user_prompt += "\n\n[IMPORTANT: Answer strictly, directly, and in the requested markdown format. Do NOT include any thinking process, reasoning, internal monologue, or analysis in your response.]"
        messages.append(Message(role="user", content=user_prompt))

        # 6. Invoke LLM with graceful fallback
        try:
            response = await self.provider.chat(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return RAGResult(
                content=response.content,
                sources=sources,
                model=response.model,
                tokens_used=response.total_tokens,
                retrieved_chunks=chunks,
            )
        except Exception as exc:
            logger.warning(f"LLM chat call failed ({exc}), generating deterministic KB response.")
            fallback_text = ContextBuilder.build_deterministic_response(query, chunks)
            return RAGResult(
                content=fallback_text,
                sources=sources,
                model="onegov-knowledge-engine-v2",
                tokens_used=len(fallback_text.split()),
                retrieved_chunks=chunks,
            )

    async def stream_answer(
        self,
        query: str,
        history: list[dict] | None = None,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> AsyncIterator[str]:
        """Stream RAG response tokens via async generator for SSE."""
        history = history or []

        # 1. Detect state from current query or history context
        state_name = detect_state(query)
        if not state_name:
            for h in reversed(history[-6:]):
                prev_state = detect_state(h.get("content", ""))
                if prev_state:
                    state_name = prev_state
                    break

        # 2. Retrieve top chunks
        chunks = await self.retriever.retrieve(query, top_k=5)
        
        # 3. Classify query
        classification = classify_query(query, chunks)

        # 4. Build Context and extract sources
        has_strong_context = len(chunks) > 0 and chunks[0].confidence >= 0.35
        
        if classification == "GENERAL":
            context_str = "No specific government knowledge base context is required for this general query."
        else:
            if not has_strong_context and not any(detect_state(c.title) or detect_state(c.chunk_text) for c in chunks):
                context_str = "No verified database records matched this query. Provide general guidance based on official Indian government processes, and instruct the user to verify all details on the official portal."
            else:
                context_str = ContextBuilder.build_context(chunks)

        system_prompt = get_system_prompt(classification, state_name, has_strong_context)

        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="system", content=context_str),
        ]

        for h in history[-12:]:
            messages.append(Message(role=h.get("role", "user"), content=h.get("content", "")))

        # Append final negative constraint to query to avoid Nemotron/Deepseek reasoning leaks
        user_prompt = query
        if classification != "GENERAL":
            user_prompt += "\n\n[IMPORTANT: Answer strictly, directly, and in the requested markdown format. Do NOT include any thinking process, reasoning, internal monologue, or analysis in your response.]"
        messages.append(Message(role="user", content=user_prompt))

        try:
            async for token in self.provider.chat_stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield token
        except Exception as exc:
            logger.warning(f"Streaming LLM failed ({exc}), yielding fallback response.")
            fallback_text = ContextBuilder.build_deterministic_response(query, chunks)
            for word in fallback_text.split(" "):
                yield word + " "
