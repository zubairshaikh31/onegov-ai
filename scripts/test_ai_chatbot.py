"""
OneGov AI — AI Chatbot Grounding & Integration Tester
"""
import sys
import json
from pathlib import Path

# Ensure stdout/stderr handles UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from ai.rag.retriever import RAGRetriever
from ai.rag.context_builder import ContextBuilder

TEST_CASES = [
    ("hello", "Hello, I need help with government services."),
    ("service_search", "Show me how to apply for a fresh passport"),
    ("scheme_search", "Tell me about Ayushman Bharat health insurance cover"),
    ("eligibility_question", "What is the eligibility criteria for PM Kisan Samman Nidhi?"),
    ("document_question", "What documents do I need to submit for a Domicile Certificate in Maharashtra?"),
    ("application_procedure", "How do I apply for a new Driving Licence?"),
    ("fee_question", "How much is the fee for fresh passport application?"),
    ("processing_time", "What is the processing time for Aadhaar card address update?"),
    ("official_portal_request", "Give me the official website link for Income Tax Return filing"),
    ("hindi_query", "आधार कार्ड में नाम कैसे सुधारें?"),
    ("mixed_hinglish_query", "Driving Licence renew karne ka kya process hai?")
]

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        print("="*70)
        print("AI CHATBOT GROUNDING & CITATIONS INTEGRATION TEST")
        print("="*70)

        retriever = RAGRetriever(session)

        for name, query in TEST_CASES:
            print(f"\nTEST CASE: {name.upper()}")
            print(f"QUERY:     '{query}'")
            
            # Retrieve chunks
            chunks = await retriever.retrieve(query, top_k=5)
            
            # Generate deterministic fallback response grounded in the chunks
            content = ContextBuilder.build_deterministic_response(query, chunks)
            sources = ContextBuilder.extract_sources(chunks)
            
            print(f"MODEL:     onegov-knowledge-engine-v2")
            print(f"RESPONSE:  {content[:500]}...")
            if len(content) > 500:
                print("           [TRUNCATED]")
            
            # Print citations/sources
            print("CITATIONS / SOURCES:")
            if not sources:
                print("  [NO CITATIONS FOUND]")
            else:
                for idx, src in enumerate(sources, 1):
                    print(f"  {idx}. [{src['type'].upper()}] {src['title']} ({src['slug']})")
                    print(f"     URL: {src['url']} (Confidence: {src['confidence']:.2f})")
            print("-"*70)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
