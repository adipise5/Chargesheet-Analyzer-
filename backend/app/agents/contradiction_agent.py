from __future__ import annotations

import re
import uuid


def contradiction_findings(chunks: list[dict]) -> list[dict]:
    times = []
    for chunk in chunks:
        for value in re.findall(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", chunk["text"]):
            times.append((value, chunk))
    distinct = sorted({value for value, _ in times})
    if len(distinct) < 2:
        return []
    citations = [{"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"],
                  "label": f"Time {value} — p{chunk['page_number']}"} for value, chunk in times[:6]]
    return [{"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "contradiction",
             "title": "Potential time inconsistency", "summary": f"The uploaded record contains differing time references ({', '.join(distinct[:6])}). Context must be reviewed before treating them as the same event.",
             "classification": "CONFLICTING_EVIDENCE", "confidence": 0.76,
             "supporting_sources": [], "contradicting_sources": citations, "entities": distinct[:6],
             "factors": {"distinct_times": len(distinct)}, "human_review_required": True, "verified": False}]

