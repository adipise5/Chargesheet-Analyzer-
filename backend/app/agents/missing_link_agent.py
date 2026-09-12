from __future__ import annotations

import uuid


def missing_link_findings(objects: list[dict], chunks_by_id: dict[str, dict]) -> list[dict]:
    findings = []
    for item in objects:
        if item["kind"] != "Evidence":
            continue
        chunk = chunks_by_id.get(item.get("data", {}).get("source_chunk", ""))
        if not chunk:
            continue
        citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"],
                    "label": f"Evidence reference — p{chunk['page_number']}"}
        findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "missing_link",
                         "title": f"Review linkage for {item['subtype']} material",
                         "summary": "The material is mentioned, but no claim link was established by deterministic extraction. No linked supporting material was located elsewhere in the uploaded record.",
                         "classification": "INSUFFICIENT_INFORMATION", "confidence": 0.6,
                         "supporting_sources": [citation], "contradicting_sources": [], "entities": [item["label"]],
                         "factors": {"linked_claims": 0}, "human_review_required": True, "verified": False})
    return findings[:6]

