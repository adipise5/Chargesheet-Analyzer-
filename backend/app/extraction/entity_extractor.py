from __future__ import annotations

import re
import uuid


PATTERNS = {
    "Vehicle": re.compile(r"\bGJ[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{3,4}\b", re.I),
    "Device": re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)"),
    "LegalSection": re.compile(r"(?:section|sec\.?|કલમ)\s*([0-9]{1,4}[A-Za-z]?)", re.I),
}

PERSON_PATTERNS = (
    ("Accused", re.compile(r"(?:name\s*&\s*age|name\s+of\s+accused)\s*:\s*([A-Z][A-Z .'-]{1,80})", re.I)),
    ("Witness", re.compile(r"\b(?:Name\s+)?([A-Z][A-Z .'-]{2,80})\s+(?:\d{1,3}\s*yrs?\.?|P\.?\s*W\.?\s*\d+|INFORMANT)\b")),
)


def extract_entities(text: str, chunk_id: str) -> list[dict]:
    found: list[dict] = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            label = match.group(0).strip()
            found.append({
                "id": f"{kind.lower()}_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + ':' + kind + ':' + label.casefold()).hex[:12]}",
                "kind": kind,
                "subtype": kind.lower(),
                "label": label,
                "confidence": 0.93,
                "data": {"source_chunk": chunk_id, "evidence_span": label},
            })
    for kind, pattern in PERSON_PATTERNS:
        for match in pattern.finditer(text):
            label = (match.group(1) or match.group(0)).strip()
            if kind == "Witness" and label.casefold() in {"name", "father", "husband"}:
                continue
            found.append({
                "id": f"{kind.lower()}_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + ':' + kind + ':' + label.casefold()).hex[:12]}",
                "kind": kind,
                "subtype": kind.lower(),
                "label": label,
                "confidence": 0.82,
                "data": {"source_chunk": chunk_id, "evidence_span": label},
            })
    return found

