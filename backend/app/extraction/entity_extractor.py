from __future__ import annotations

import re
import uuid

GUJARATI_NUMERALS = "૦૧૨૩૪૫૬૭૮૯"
NUMERALS = f"0-9{GUJARATI_NUMERALS}"

PATTERNS = {
    "Vehicle": re.compile(r"\bGJ[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{3,4}\b", re.I),
    "Device": re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)"),
    # Gujarati legal documents commonly print the section number using Gujarati
    # numerals (for example, ``કલમ ૨૨૩``). Keep the original span for review.
}
LEGAL_SECTION_BLOCK = re.compile(
    rf"(?<![A-Za-z])(?:sections?|secs?\.?|ss\.?)(?![A-Za-z])\s*:?[ \t]*"
    rf"([{NUMERALS}]{{1,4}}[A-Za-z]?(?:[ \t]*(?:,|and|&)\s*[{NUMERALS}]{{1,4}}[A-Za-z]?)*)(?![A-Za-z])|"
    rf"(કલમ)\s*:?[ \t]*([{NUMERALS}]{{1,4}}[A-Za-z]?)",
    re.I,
)
LEGAL_SECTION_NUMBER = re.compile(rf"(?<![{NUMERALS}A-Za-z])([{NUMERALS}]{{1,4}}[A-Za-z]?)(?![{NUMERALS}A-Za-z])")

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
    for block in LEGAL_SECTION_BLOCK.finditer(text):
        number_text = block.group(1) or block.group(3)
        if not number_text:
            continue
        prefix = "કલમ" if block.group(2) else block.group(0)[:block.start(1) - block.start()].strip()
        for number in LEGAL_SECTION_NUMBER.finditer(number_text):
            label = f"{prefix} {number.group(1)}"
            found.append({
                "id": f"legalsection_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + ':LegalSection:' + label.casefold()).hex[:12]}",
                "kind": "LegalSection", "subtype": "legal_section", "label": label, "confidence": 0.93,
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

