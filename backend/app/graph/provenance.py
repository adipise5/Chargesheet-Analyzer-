from __future__ import annotations

from app.schemas.citation import Citation


def citation_from_chunk(chunk: dict, label: str | None = None) -> Citation:
    return Citation(
        document_id=chunk["document_id"],
        page=int(chunk["page_number"]),
        chunk_id=chunk["id"],
        label=label or f"Source page {chunk['page_number']}",
    )


def citations_are_valid(citations: list[dict], known_chunk_ids: set[str]) -> bool:
    return bool(citations) and all(c.get("chunk_id") in known_chunk_ids and int(c.get("page", 0)) >= 1 for c in citations)

