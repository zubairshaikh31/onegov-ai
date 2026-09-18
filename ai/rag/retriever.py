"""
OneGov AI — Hybrid RAG Retriever.

Retrieves the most relevant verified knowledge chunks using a fuse of:
  1. pgvector cosine search (real semantic embeddings)
  2. PostgreSQL full-text search (ts_rank over GIN-indexed tsvector)
  3. pg_trgm similarity (robust to spelling errors)

Results are merged with Reciprocal Rank Fusion (RRF), then reranked with
source-authority boosts (verification status, official source, freshness)
and given a normalised confidence score used for AI grounding.

If real embeddings are unavailable the retrieval degrades to FTS + trigram.
It never fabricates vectors.
"""

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any

from loguru import logger
from sqlalchemy import func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.government import KnowledgeChunk

RRF_K = 60

EXPANSION_RULES = {
    r"\bdriving\b": ["driving licence", "driving license", "learner's licence", "sarathi parivahan"],
    r"\baadhaar\b": ["aadhaar enrolment & update", "uidai", "aadhaar update"],
    r"\badhar\b": ["aadhaar", "uidai"],
    r"\bhealth card\b": ["ayushman bharat pm-jay", "abha", "pmjay"],
    r"\bhealth insurance\b": ["ayushman bharat pm-jay"],
    r"\bcaste\b": ["caste certificate", "revenue department"],
    r"\bration\b": ["ration card", "pds", "food security"],
    r"\bpension\b": ["welfare scheme pension", "national pension system"],
    r"\bpan card\b": ["pan enrolment", "nsdl", "utiitsl"]
}


@dataclass
class RetrievedChunk:
    id: str
    entity_type: str
    entity_id: str | None
    entity_slug: str | None
    title: str
    chunk_text: str
    score: float
    metadata: dict[str, Any]
    confidence: float = 0.0


class RAGRetriever:
    """Retrieves top relevant knowledge chunks for a user query."""

    def __init__(self, db: AsyncSession | None = None, embedding_service: Any = None) -> None:
        self.db = db
        self._embedder = embedding_service

    def _get_embedder(self):
        if self._embedder is None:
            from ai.embeddings.embedder import get_embedding_service
            self._embedder = get_embedding_service()
        return self._embedder

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        entity_type: str | None = None,
        entity_slug: str | None = None,
    ) -> list[RetrievedChunk]:
        query = (query or "").strip()
        if not query:
            return []

        # Query expansion for FTS and similarity searches
        expanded_terms = []
        query_lower = query.lower()
        for pattern, terms in EXPANSION_RULES.items():
            if re.search(pattern, query_lower):
                expanded_terms.extend(terms)

        search_query = query
        if expanded_terms:
            unique_expanded = []
            for t in expanded_terms:
                if t not in unique_expanded and t not in query_lower:
                    unique_expanded.append(t)
            if unique_expanded:
                search_query = f"{query} {' '.join(unique_expanded)}"
                logger.debug(f"Expanded query: '{query}' -> '{search_query}'")

        if self.db is None:
            return self._search_knowledge_files(search_query, top_k)

        matches: dict[str, RetrievedChunk] = {}
        ranks: dict[str, int] = {}

        base_filters = [
            KnowledgeChunk.deleted_at.is_(None),
            KnowledgeChunk.is_active.is_(True),
        ]
        if entity_type:
            base_filters.append(KnowledgeChunk.entity_type == entity_type)
        if entity_slug:
            base_filters.append(KnowledgeChunk.entity_slug == entity_slug)

        # 1 ── Vector search (real embeddings) ───────────────────────────────
        query_vec: list[float] | None = None
        try:
            query_vec = await self._get_embedder().embed_one(query)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Embedding unavailable, skipping vector search: {exc}")

        rank_counter = 0
        if query_vec:
            try:
                vec_stmt = (
                    select(
                        KnowledgeChunk.id,
                        KnowledgeChunk.entity_type,
                        KnowledgeChunk.entity_id,
                        KnowledgeChunk.entity_slug,
                        KnowledgeChunk.title,
                        KnowledgeChunk.chunk_text,
                        KnowledgeChunk.metadata_,
                        KnowledgeChunk.verification_status
                        if hasattr(KnowledgeChunk, "verification_status") else literal("UNVERIFIED"),
                        KnowledgeChunk.embedding_model,
                        (1.0 - KnowledgeChunk.embedding.cosine_distance(query_vec)).label("sim"),
                    )
                    .where(*base_filters)
                    .order_by(KnowledgeChunk.embedding.cosine_distance(query_vec))
                    .limit(top_k * 4)
                )
                rows = (await self.db.execute(vec_stmt)).all()
                for idx, r in enumerate(rows):
                    rank_counter += 1
                    self._merge(
                        matches, ranks,
                        RetrievedChunk(
                            id=str(r.id),
                            entity_type=r.entity_type,
                            entity_id=str(r.entity_id) if r.entity_id else None,
                            entity_slug=r.entity_slug,
                            title=r.title,
                            chunk_text=r.chunk_text,
                            score=float(r.sim) if r.sim is not None else 0.0,
                            metadata=dict(r.metadata_) if r.metadata_ else {},
                        ),
                        rank_counter,
                        list_order=len(matches),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Vector query failed ({exc}), continuing with text search.")

        # 2 ── Full-text search ──────────────────────────────────────────────
        try:
            fts_query = func.plainto_tsquery("english", search_query)
            fts_expr = func.ts_rank_cd(
                func.to_tsvector("english", KnowledgeChunk.title + " " + KnowledgeChunk.chunk_text),
                fts_query,
            ).label("ts_rank")
            fts_stmt = (
                select(
                    KnowledgeChunk.id,
                    KnowledgeChunk.entity_type,
                    KnowledgeChunk.entity_id,
                    KnowledgeChunk.entity_slug,
                    KnowledgeChunk.title,
                    KnowledgeChunk.chunk_text,
                    KnowledgeChunk.metadata_,
                    fts_expr,
                )
                .where(*base_filters, fts_query.op("@@")(func.to_tsvector(
                    "english", KnowledgeChunk.title + " " + KnowledgeChunk.chunk_text
                )))
                .order_by(fts_expr.desc())
                .limit(top_k * 4)
            )
            rows = (await self.db.execute(fts_stmt)).all()
            for idx, r in enumerate(rows):
                rank_counter += 1
                self._merge(
                    matches, ranks,
                    RetrievedChunk(
                        id=str(r.id),
                        entity_type=r.entity_type,
                        entity_id=str(r.entity_id) if r.entity_id else None,
                        entity_slug=r.entity_slug,
                        title=r.title,
                        chunk_text=r.chunk_text,
                        score=float(r.ts_rank) if r.ts_rank is not None else 0.0,
                        metadata=dict(r.metadata_) if r.metadata_ else {},
                    ),
                    rank_counter,
                    list_order=len(matches),
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"FTS query failed ({exc}).")

        # 3 ── Trigram search (typo tolerance) ───────────────────────────────
        try:
            trig_stmt = (
                select(
                    KnowledgeChunk.id,
                    KnowledgeChunk.entity_type,
                    KnowledgeChunk.entity_id,
                    KnowledgeChunk.entity_slug,
                    KnowledgeChunk.title,
                    KnowledgeChunk.chunk_text,
                    KnowledgeChunk.metadata_,
                    func.greatest(
                        func.similarity(KnowledgeChunk.title, search_query),
                        func.similarity(func.coalesce(func.substr(KnowledgeChunk.chunk_text, 1, 800)), search_query),
                    ).label("trgm"),
                )
                .where(*base_filters)
                .order_by(func.greatest(
                    func.similarity(KnowledgeChunk.title, search_query),
                    func.similarity(func.coalesce(func.substr(KnowledgeChunk.chunk_text, 1, 800)), search_query),
                ).desc())
                .limit(top_k * 4)
            )
            rows = (await self.db.execute(trig_stmt)).all()
            for idx, r in enumerate(rows):
                rank_counter += 1
                self._merge(
                    matches, ranks,
                    RetrievedChunk(
                        id=str(r.id),
                        entity_type=r.entity_type,
                        entity_id=str(r.entity_id) if r.entity_id else None,
                        entity_slug=r.entity_slug,
                        title=r.title,
                        chunk_text=r.chunk_text,
                        score=float(r.trgm) if r.trgm is not None else 0.0,
                        metadata=dict(r.metadata_) if r.metadata_ else {},
                    ),
                    rank_counter,
                    list_order=len(matches),
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Trigram query failed ({exc}).")

        if not matches:
            return self._search_knowledge_files(query, top_k)

        reranked = self._rerank(matches, ranks)
        for chunk in reranked:
            chunk.confidence = self._confidence(chunk)
        return reranked[:top_k]

    # ── Fusion & reranking helpers ────────────────────────────────────────────

    def _merge(
        self,
        matches: dict[str, RetrievedChunk],
        ranks: dict[str, int],
        chunk: RetrievedChunk,
        rank: int,
        list_order: int,
    ) -> None:
        key = chunk.id
        if key not in ranks:
            ranks[key] = rank
            chunk.metadata["_list_order"] = list_order
            matches[key] = chunk
        else:
            # keep the higher-scoring match if it appears more than once
            existing = matches[key]
            if chunk.score > existing.score:
                existing.score = chunk.score
                existing.chunk_text = chunk.chunk_text
                existing.metadata.update(chunk.metadata)

    def _rerank(self, matches: dict[str, RetrievedChunk], ranks: dict[str, int]) -> list[RetrievedChunk]:
        chunks = list(matches.values())
        for chunk in chunks:
            rank = ranks[chunk.id]
            rrf = 1.0 / (RRF_K + rank)
            alpha = chunk.score if chunk.score and chunk.score >= 0 else 0.0
            combined = rrf * 1.0 + min(alpha, 1.0) * 0.1
            combined += self._authority_boost(chunk.metadata)
            chunk.metadata.pop("_list_order", None)
            chunk.score = round(combined, 4)
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks

    def _authority_boost(self, metadata: dict[str, Any]) -> float:
        boost = 0.0
        verification = (metadata.get("verification_status") or "UNVERIFIED").upper()
        if verification == "VERIFIED":
            boost += 0.06
        elif verification == "PARTIALLY_VERIFIED":
            boost += 0.03
        if metadata.get("official_source"):
            boost += 0.02
        return boost

    def _confidence(self, chunk: RetrievedChunk) -> float:
        """0–1 confidence based on score, verification status and source presence."""
        verification = (chunk.metadata.get("verification_status") or "UNVERIFIED").upper()
        base = min(max(chunk.score, 0.0), 1.0)
        contrib = {"VERIFIED": 0.35, "PARTIALLY_VERIFIED": 0.25, "STALE": 0.15,
                   "CONFLICTING": 0.1, "UNVERIFIED": 0.05, "ARCHIVED": 0.02}.get(verification, 0.05)
        url_bonus = 0.1 if chunk.metadata.get("official_url") else 0.0
        return round(min(base + contrib + url_bonus, 1.0), 2)

    # ── Fallback (database unavailable) ───────────────────────────────────────

    def _search_knowledge_files(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """In-memory keyword search across knowledge files when DB is unavailable."""
        from pathlib import Path

        kb_dirs = [
            Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "knowledge",
            Path(__file__).resolve().parent.parent / "knowledge",
        ]
        kb_dir = next((d for d in kb_dirs if d.exists()), None)
        if not kb_dir:
            return []

        words = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[float, RetrievedChunk]] = []

        svc_dir = kb_dir / "services"
        if svc_dir.exists():
            for f in svc_dir.glob("*.json"):
                try:
                    import json

                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    text_content = (
                        f"{data.get('name', '')} {data.get('description', '')} "
                        f"{data.get('eligibility', '')} {data.get('fees', '')}"
                    )
                    text_words = set(re.findall(r"\w+", text_content.lower()))
                    overlap = len(words.intersection(text_words))
                    if overlap > 0:
                        score = overlap / max(1, len(words))
                        chunk = RetrievedChunk(
                            id=f"svc:{f.stem}",
                            entity_type="service",
                            entity_id=None,
                            entity_slug=slugify(data.get("name", f.stem)),
                            title=f"Service: {data.get('name', f.stem)}",
                            chunk_text=text_content[:1500],
                            score=score,
                            metadata={
                                "service_name": data.get("name"),
                                "official_url": data.get("official_portal"),
                                "eligibility": data.get("eligibility"),
                            },
                        )
                        scored.append((score, chunk))
                except Exception:  # noqa: BLE001
                    continue

        scored.sort(key=lambda x: x[0], reverse=True)
        result = [item[1] for item in scored[:top_k]]
        for chunk in result:
            chunk.confidence = round(min(chunk.score * 0.6, 0.6), 2)
        return result


def slugify(text_val: str) -> str:
    text_val = (text_val or "").lower().strip()
    text_val = re.sub(r"[^\w\s-]", "", text_val)
    text_val = re.sub(r"[\s_-]+", "-", text_val)
    return text_val.strip("-")


def generate_embedding_vector(text_content: str, dim: int = 768) -> list[float]:
    """
    DEPRECATED — legacy deterministic hash vector. Kept only for tests/backward
    compat. Production retrieval uses real embeddings via EmbeddingService.
    """
    if not text_content:
        return [0.0] * dim
    words = re.findall(r"\w+", text_content.lower())
    vec = [0.0] * dim
    for i, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        pos_weight = 1.0 / (1.0 + math.log(i + 1))
        vec[idx] += pos_weight * 1.5
        vec[(idx + 137) % dim] += pos_weight * 0.8
        vec[(idx + 311) % dim] += pos_weight * 0.4
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return vec