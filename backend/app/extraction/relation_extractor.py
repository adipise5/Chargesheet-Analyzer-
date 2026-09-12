from __future__ import annotations

import uuid


def provenance_relation(case_id: str, source_id: str, chunk: dict, citation: dict) -> dict:
    return {
        "id": f"rel_{uuid.uuid5(uuid.NAMESPACE_URL, source_id + chunk['id']).hex[:12]}",
        "case_id": case_id,
        "source_id": source_id,
        "target_id": chunk["id"],
        "relation": "SOURCE_OF",
        "confidence": 1.0,
        "citations": [citation],
        "extraction_method": "deterministic",
        "human_verified": False,
    }

