from __future__ import annotations

import re
import uuid


TEMPLATE_MARKERS = (
    "final investigation report", "final report/charge sheet", "charge sheet no",
    "nature of final report", "details of the examined witnesses", "mock trial",
)


def extract_claims(text: str, chunk_id: str) -> list[dict]:
    """Extract source-anchored candidate claims; local LLM enrichment is optional."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if len(s.strip()) >= 24]
    claims = []
    for sentence in sentences[:12]:
        lowered = sentence.casefold()
        if any(marker in lowered for marker in TEMPLATE_MARKERS) or (
            "property" in lowered and "value" in lowered and ("recovered" in lowered or "police station" in lowered)
        ):
            continue
        if any(word in lowered for word in ("stated", "saw", "observed", "recovered", "seized", "જણાવ", "જોઈ", "કબજે")):
            claims.append({
                "id": f"claim_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + sentence).hex[:12]}",
                "kind": "Claim", "subtype": "source_claim", "label": sentence[:120],
                "confidence": 0.72, "data": {"text": sentence, "source_chunk": chunk_id},
            })
    return claims

