from __future__ import annotations

import uuid

from app.extraction.claim_extractor import extract_claims
from app.extraction.entity_extractor import extract_entities
from app.extraction.evidence_extractor import extract_evidence
from app.extraction.event_extractor import extract_events


def build_graph(case: dict, documents: list[dict], chunks: list[dict]) -> tuple[list[dict], list[dict]]:
    objects: list[dict] = [{"id": case["id"], "kind": "Case", "subtype": "case", "label": case["case_number"],
                           "confidence": 1.0, "data": {"police_station": case["police_station"]}}]
    relations: list[dict] = []
    for document in documents:
        objects.append({"id": document["id"], "kind": "Document", "subtype": document["category"],
                        "label": document["filename"], "confidence": 1.0,
                        "data": {"category": document["category"], "page_count": document["page_count"]}})
        relations.append({"id": f"rel_{uuid.uuid4().hex[:12]}", "case_id": case["id"], "source_id": document["id"],
                          "target_id": case["id"], "relation": "PART_OF", "confidence": 1.0,
                          "citations": [], "extraction_method": "system", "human_verified": True})
    seen = {item["id"] for item in objects}
    for chunk in chunks:
        citation = {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"],
                    "label": f"{chunk.get('document_label', 'Document')} — p{chunk['page_number']}"}
        chunk_obj = {"id": chunk["id"], "kind": "TextChunk", "subtype": "source", "label": f"Page {chunk['page_number']} source",
                     "confidence": chunk.get("confidence", 1.0),
                     "data": {"document_id": chunk["document_id"], "page_number": chunk["page_number"], "language": chunk["language"]}}
        objects.append(chunk_obj)
        relations.append({"id": f"rel_{uuid.uuid4().hex[:12]}", "case_id": case["id"], "source_id": chunk["id"],
                          "target_id": chunk["document_id"], "relation": "PART_OF", "confidence": 1.0,
                          "citations": [], "extraction_method": "system", "human_verified": True})
        extracted = extract_entities(chunk["text"], chunk["id"]) + extract_claims(chunk["text"], chunk["id"]) + extract_events(chunk["text"], chunk["id"]) + extract_evidence(chunk["text"], chunk["id"])
        for item in extracted:
            if item["id"] not in seen:
                objects.append(item)
                seen.add(item["id"])
            relations.append({"id": f"rel_{uuid.uuid4().hex[:12]}", "case_id": case["id"], "source_id": item["id"],
                              "target_id": chunk["id"], "relation": "SOURCE_OF", "confidence": item["confidence"],
                              "citations": [citation], "extraction_method": "deterministic", "human_verified": False})
    return objects, relations

