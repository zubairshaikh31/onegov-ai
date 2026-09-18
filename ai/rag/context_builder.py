"""
OneGov AI — RAG Context Builder
Assembles retrieved knowledge base chunks into structured prompt context.
"""

from typing import Any
from ai.rag.retriever import RetrievedChunk


class ContextBuilder:
    """Formats retrieved chunks into clear, structured context for the LLM."""

    @staticmethod
    def build_context(chunks: list[RetrievedChunk]) -> str:
        """Construct structured markdown context block."""
        if not chunks:
            return "No specific government knowledge records matched this query. Advise the citizen based on general official Indian government procedures."

        context_lines = [
            "### VERIFIED GOVERNMENT KNOWLEDGE BASE RECORDS:",
            "Use ONLY the following factual records to answer the citizen's query. Do not invent details.",
            "",
        ]

        for i, chunk in enumerate(chunks, 1):
            context_lines.append(f"--- RECORD {i} [{chunk.entity_type.upper()}]: {chunk.title} ---")
            context_lines.append(chunk.chunk_text.strip())
            if chunk.metadata:
                meta_strs = []
                if "official_url" in chunk.metadata and chunk.metadata["official_url"]:
                    meta_strs.append(f"Official Portal: {chunk.metadata['official_url']}")
                if "beneficiary" in chunk.metadata and chunk.metadata["beneficiary"]:
                    meta_strs.append(f"Beneficiary: {chunk.metadata['beneficiary']}")
                if meta_strs:
                    context_lines.append(" | ".join(meta_strs))
            context_lines.append("")

        return "\n".join(context_lines)

    @staticmethod
    def extract_sources(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
        """Extract structured sources list for frontend citation display."""
        sources = []
        seen = set()

        for c in chunks:
            key = c.entity_slug or c.title
            if key in seen:
                continue
            seen.add(key)

            url = c.metadata.get("official_url") if c.metadata else None
            slug = c.entity_slug or ""
            if not url and slug:
                url = f"/services/{slug}" if c.entity_type == "service" else f"/schemes/{slug}"

            sources.append({
                "title": c.title.replace("Service: ", "").replace("Welfare Scheme: ", "").replace("FAQ: ", ""),
                "type": c.entity_type,
                "slug": slug,
                "url": url or f"/services/{slug}",
                "confidence": round(c.score, 2),
            })

        return sources[:4]

    @staticmethod
    def build_deterministic_response(query: str, chunks: list[RetrievedChunk]) -> str:
        """
        Build a high quality, structured factual response directly from KB chunks.
        Used as fallback when LLM server is starting or offline.
        """
        if not chunks:
            return (
                f"I couldn't find an exact match for **\"{query}\"** in our active database.\n\n"
                "Please try searching for common services like **Passport Seva, Aadhaar Update, Driving Licence, PAN Card, PM Kisan**, or browse our [Services Directory](/services)."
            )

        top_chunk = chunks[0]
        meta = top_chunk.metadata or {}
        portal = meta.get("official_url", "https://india.gov.in")
        service_name = meta.get("service_name") or top_chunk.title.replace("Service Overview: ", "")

        lines = [
            f"### 🏛️ {service_name}",
            "",
            top_chunk.chunk_text.strip(),
            "",
            "#### 📋 Key Requirements & Next Steps:",
            "• **Official Portal:** [" + portal + "](" + portal + ")",
            "• **Mode:** Available online and at designated citizen service centers.",
            "• **Assistance:** You can also ask specific questions about required documents or eligibility criteria.",
        ]

        if len(chunks) > 1:
            lines.append("\n#### 🔗 Related Government Resources:")
            for c in chunks[1:4]:
                lines.append(f"• **{c.title}** ({c.entity_type.title()})")

        return "\n".join(lines)
