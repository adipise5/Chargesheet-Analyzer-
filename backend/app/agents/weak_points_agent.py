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
        claim = " ".join(item["label"].split())[:180]
        findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "weak_point",
                         # A raw sentence can be a truncated OCR fragment
                         # (for example, ending in "for"), which is not a
                         # useful heading. Keep the exact claim in the body
                         # and use a stable, source-grounded title instead.
                         "title": f"Single-source claim on page {chunk['page_number']}",
                         "summary": f"This extracted claim — {claim} — is linked to only one source passage (page {chunk['page_number']}). No second document or independent supporting link was located in the uploaded record.",
                         "classification": "LIMITED_CORROBORATION", "confidence": 0.68,
                         "supporting_sources": [citation], "contradicting_sources": [], "entities": [],
                         "factors": {"number_of_supporting_sources": 1, "number_of_independent_source_types": 1},
                         "human_review_required": True, "verified": False,
                         "why_important": "A single-source claim may be challenged as uncorroborated if no independent record supports it.",
                         "recommended_correction": "Check the FIR, witness statements, medical/forensic records, seizure memo, and digital material for independent support; qualify the claim if none exists.",
                         "io_action": f"Review the source passage on page {chunk['page_number']} and record which independent document or witness, if any, corroborates this claim.",
                         "defense_questions": ["What independent evidence corroborates this claim?", f"Why is this claim presently supported only by page {chunk['page_number']}?"]})
    return findings[:8]

