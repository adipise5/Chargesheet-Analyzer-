from __future__ import annotations

import re
import uuid

EVIDENCE_TYPES = {
    "digital": ("cctv", "cdr", "phone", "mobile", "video", "digital"),
    "forensic": ("fsl", "forensic", "dna", "fingerprint"),
    "physical": ("weapon", "vehicle", "seized", "recovered", "કબજે"),
    "documentary": ("report", "record", "memo", "panchnama", "પંચનામું"),
    "witness": ("witness", "statement", "સાક્ષી"),
}


def extract_evidence(text: str, chunk_id: str) -> list[dict]:
    found = []
    for sentence in [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]:
        lower = sentence.casefold()
        for subtype, terms in EVIDENCE_TYPES.items():
            if any(term in lower for term in terms):
                found.append({
                    "id": f"evidence_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + subtype + sentence).hex[:12]}",
                    "kind": "Evidence", "subtype": subtype, "label": sentence[:120],
                    "confidence": 0.7, "data": {"description": sentence, "source_chunk": chunk_id},
                })
                break
    return found[:16]

