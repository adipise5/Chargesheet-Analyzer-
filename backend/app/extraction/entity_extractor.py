from __future__ import annotations

import re
import uuid


PATTERNS = {
    "Vehicle": re.compile(r"\bGJ[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{3,4}\b", re.I),
    "Device": re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)"),
    "LegalSection": re.compile(r"(?:section|sec\.?|કલમ)\s*([0-9]{1,4}[A-Za-z]?)", re.I),
}


def extract_entities(text: str, chunk_id: str) -> list[dict]:
    found: list[dict] = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            label = match.group(0).strip()
            found.append({
                "id": f"{kind.lower()}_{uuid.uuid5(uuid.NAMESPACE_URL, kind + ':' + label.casefold()).hex[:12]}",
                "kind": kind,
                "subtype": kind.lower(),
                "label": label,
                "confidence": 0.93,
                "data": {"source_chunk": chunk_id, "evidence_span": label},
            })
    return found

