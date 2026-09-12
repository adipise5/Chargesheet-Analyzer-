from __future__ import annotations

import re
import uuid

EVIDENCE_TYPES = {
    "digital": ("cctv", "cdr", "phone", "mobile", "video", "digital"),
    "forensic": ("fsl", "forensic", "dna", "fingerprint"),
    "physical": ("weapon", "vehicle", "seized", "recovered", "કબજે"),
    "documentary": ("memo", "panchnama", "annexure", "inquest", "પંચનામું"),
    "witness": ("witness statement", "statement of", "eyewitness", "સાક્ષી"),
}

EVIDENCE_WORDS = {
    subtype: tuple(re.compile(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])") for term in terms)
    for subtype, terms in EVIDENCE_TYPES.items()
}

# Common form and template fragments are not evidence merely because they contain
# generic words such as "report", "record", "recovered", or "witness".
TEMPLATE_MARKERS = (
    "final investigation report", "final report/charge sheet", "charge sheet no",
    "nature of final report", "property value", "police station recovered from",
    "record diary", "details of the examined witnesses", "mock trial",
)


def extract_evidence(text: str, chunk_id: str) -> list[dict]:
    found = []
    for sentence in [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]:
        lower = sentence.casefold()
        if any(marker in lower for marker in TEMPLATE_MARKERS) or (
            "property" in lower and "value" in lower and ("recovered" in lower or "police station" in lower)
        ):
            continue
        for subtype, terms in EVIDENCE_TYPES.items():
            if any(pattern.search(lower) for pattern in EVIDENCE_WORDS[subtype]):
                found.append({
                    "id": f"evidence_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + subtype + sentence).hex[:12]}",
                    "kind": "Evidence", "subtype": subtype, "label": sentence[:120],
                    "confidence": 0.7, "data": {"description": sentence, "source_chunk": chunk_id},
                })
                break
    return found[:16]

