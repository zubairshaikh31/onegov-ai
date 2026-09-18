"""
OneGov AI — RAG Retrieval Audit Tool
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.models.government import KnowledgeChunk
from ai.rag.retriever import RAGRetriever

TEST_QUERIES = [
    "Aadhaar address update",
    "driving licence renewal",
    "farmer schemes",
    "student scholarship",
    "income certificate",
    "birth certificate"
]

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        # 1. Inspect Knowledge Chunks in DB
        total_chunks = (await session.execute(select(func.count(KnowledgeChunk.id)))).scalar()
        embedded_chunks = (await session.execute(select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.embedding.is_not(None)))).scalar()
        
        print("="*60)
        print("RAG INGESTION AUDIT")
        print("="*60)
        print(f"Total Knowledge Chunks:       {total_chunks}")
        print(f"Embedded Chunks (in DB):      {embedded_chunks}")
        print(f"Missing Embeddings:           {total_chunks - embedded_chunks}")
        print(f"Embedding Model Configured:   {settings.EMBEDDING_MODEL}")
        print(f"Embedding Dimensions:         {settings.EMBEDDING_DIM}")
        print(f"pgvector Extension Enabled:   {settings.USE_PGVECTOR}")
        
        # Check if embeddings are real (non-empty vector containing double floats)
        is_real = "NO (FTS Fallback Active)"
        if embedded_chunks > 0:
            first_chunk = (await session.execute(select(KnowledgeChunk).where(KnowledgeChunk.embedding.is_not(None)).limit(1))).scalar()
            if first_chunk and len(first_chunk.embedding) == settings.EMBEDDING_DIM:
                # Real float array check
                if any(x != 0.0 for x in first_chunk.embedding):
                    is_real = "YES (Real Vector Embeddings present in PostgreSQL)"
        print(f"Are Embeddings Real Vectors:  {is_real}")
        print("="*60)

        # 2. Test RAG Retriever queries
        retriever = RAGRetriever(db=session)
        print("\n" + "="*60)
        print("RAG RETRIEVAL TESTING (HYBRID FUSION SEARCH)")
        print("="*60)

        for query in TEST_QUERIES:
            print(f"\nQUERY: '{query}'")
            results = await retriever.retrieve(query, top_k=3)
            if not results:
                print("  [NO RESULTS RETRIEVED]")
                continue
            
            for i, r in enumerate(results, 1):
                print(f"  {i}. Title: {r.title}")
                print(f"     Entity: {r.entity_type} ({r.entity_slug})")
                print(f"     Score:  {r.score:.4f} | Confidence: {r.confidence:.4f}")
                # Print short snippet
                snippet = r.chunk_text[:120].replace('\n', ' ') + "..."
                print(f"     Text:   {snippet}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
