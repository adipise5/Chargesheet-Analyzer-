from __future__ import annotations

import uuid


def strong_findings(objects: list[dict], chunks_by_id: dict[str, dict]) -> list[dict]:
    # A deterministic D1 profile: multiple different evidence subtypes on one source-backed record.
    by_chunk: dict[str, list[dict]] = {}
    for item in objects:
        if item["kind"] == "Evidence":
            by_chunk.setdefault(item.get("data", {}).get("source_chunk", ""), []).append(item)
    findings = []
    for chunk_id, evidence in by_chunk.items():
        subtypes = {item["subtype"] for item in evidence}
        chunk = chunks_by_id.get(chunk_id)
        if chunk and len(subtypes) >= 2:
            citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk_id,
                        "label": f"Source material — p{chunk['page_number']}"}
            findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "strong_point",
                             "title": "Multiple evidence categories recorded together",
                             "summary": "The source passage links more than one evidence category. This is source-backed but independence must be confirmed by an investigator.",
                             "classification": "MODERATELY_CORROBORATED", "confidence": 0.72,
                             "supporting_sources": [citation], "contradicting_sources": [],
                             "entities": [item["label"] for item in evidence[:3]],
                             "factors": {"number_of_supporting_sources": 1, "number_of_independent_source_types": len(subtypes)},
                             "human_review_required": True, "verified": False})
    return findings[:8]

