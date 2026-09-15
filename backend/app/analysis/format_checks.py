from __future__ import annotations

import re
import uuid


def draft_quality_findings(documents: list[dict], chunks: list[dict]) -> list[dict]:
    drafts = {doc["id"] for doc in documents if doc.get("role") == "draft_chargesheet" or doc.get("category") == "chargesheet"}
    if not drafts:
        return []
    draft_chunks = [chunk for chunk in chunks if chunk["document_id"] in drafts]
    findings = []
    for chunk in draft_chunks:
        lines = chunk["text"].splitlines()
        # Only use top-level form numbering. Indented sub-items (for example a
        # list of statutory sections) are not a continuation of the form's
        # paragraph sequence. PDFs also commonly OCR `2.` as `2,`.
        numbers = [int(match.group(1)) for line in lines if (match := re.match(r"\s{0,3}(\d+)(?:[.,)]|\s{2,})\s+", line))]
        expected = None
        has_gap = False
        for value in numbers:
            if expected is None:
                expected = value + 1
            elif value < expected:
                # A reset is usually an indented sub-list flattened by PDF text
                # extraction; keep tracking the outer form sequence instead.
                continue
            elif value == expected:
                expected += 1
            else:
                has_gap = True
                break
        if len(numbers) >= 3 and has_gap:
            citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"], "label": f"Numbering check — p{chunk['page_number']}"}
            findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "potential_mistake", "title": "Possible paragraph numbering gap",
                             "summary": f"Numbered paragraphs on page {chunk['page_number']} are not sequential. This may be a drafting or formatting error and must be checked against the official template.",
                             "classification": "REVIEW_REQUIRED", "confidence": 0.65, "supporting_sources": [citation], "contradicting_sources": [],
                             "entities": [], "factors": {"numbered_items": len(numbers)}, "human_review_required": True, "verified": False})
    full_text = " ".join(chunk["text"] for chunk in draft_chunks)
    if draft_chunks and not re.search(r"\b(?:u\s*/\s*s\.?|under\s+section|section|sec\.?|કલમ)\s*[:.-]?\s*\d", full_text, re.I):
        chunk = draft_chunks[0]
        citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"], "label": f"Chargesheet section check — p{chunk['page_number']}"}
        findings.append({"id": f"finding_{uuid.uuid4().hex[:10]}", "type": "missing_link", "title": "No statutory section reference detected in draft",
                         "summary": "The draft chargesheet does not contain a recognizable section reference. Confirm that the legal sections are present and correctly recorded; this detector does not assess legal applicability.",
                         "classification": "REVIEW_REQUIRED", "confidence": 0.6, "supporting_sources": [citation], "contradicting_sources": [],
                         "entities": [], "factors": {"section_reference_detected": False}, "human_review_required": True, "verified": False})
    return findings[:8]
