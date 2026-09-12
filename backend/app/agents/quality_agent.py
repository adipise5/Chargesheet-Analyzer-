from __future__ import annotations

import re
import uuid
from collections import defaultdict


def quality_findings(chunks: list[dict]) -> list[dict]:
    vehicles: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    pattern = re.compile(r"\bGJ[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{3,4}\b", re.I)
    for chunk in chunks:
        for match in pattern.findall(chunk["text"]):
            canonical = re.sub(r"[^A-Z0-9]", "", match.upper())
            vehicles[canonical[:6]].append((canonical, chunk))
    findings = []
    for variants in vehicles.values():
        values = {value for value, _ in variants}
        if len(values) < 2:
            continue
        citations = [{"document_id": c["document_id"], "page": c["page_number"], "chunk_id": c["id"],
                      "label": f"Vehicle mention {v} — p{c['page_number']}"} for v, c in variants]
        findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "potential_mistake",
                         "title": "Potential vehicle registration mismatch",
                         "summary": f"Similar vehicle identifiers appear with different characters: {', '.join(sorted(values))}. Human review is required.",
                         "classification": "REVIEW_REQUIRED", "confidence": 0.82,
                         "supporting_sources": citations, "contradicting_sources": [], "entities": sorted(values),
                         "factors": {"variant_count": len(values)}, "human_review_required": True, "verified": False})
    return findings

