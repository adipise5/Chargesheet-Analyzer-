from __future__ import annotations

import uuid


def weak_findings(objects: list[dict], chunks_by_id: dict[str, dict]) -> list[dict]:
    findings = []
    for item in objects:
        if item["kind"] != "Claim":
            continue
        chunk = chunks_by_id.get(item.get("data", {}).get("source_chunk", ""))
        if not chunk:
            continue
        citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"],
                    "label": f"Single located source — p{chunk['page_number']}"}
        findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "weak_point",
                         "title": item["label"][:100],
                         "summary": "This candidate claim is presently linked to a single source passage. No linked supporting material was located in the uploaded record.",
                         "classification": "LIMITED_CORROBORATION", "confidence": 0.68,
                         "supporting_sources": [citation], "contradicting_sources": [], "entities": [],
                         "factors": {"number_of_supporting_sources": 1, "number_of_independent_source_types": 1},
                         "human_review_required": True, "verified": False})
    return findings[:8]

