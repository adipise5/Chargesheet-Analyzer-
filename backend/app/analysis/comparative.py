from __future__ import annotations

import re
import uuid
from collections import defaultdict

from app.extraction.date_utils import GUJARATI_DIGITS, normalize_date


FIELD_PATTERNS = {
    "vehicle number": re.compile(r"\bGJ[- ]?\d{1,2}[- ]?[A-Z]{1,3}[- ]?\d{3,4}\b", re.I),
    "date": re.compile(r"(?<!\w)[0-9૦૧૨૩૪૫૬૭૮૯]{1,4}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,2}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,4}(?!\w)"),
    "time": re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"),
    "mobile number": re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)"),
    "legal section": re.compile(r"(?:section|sec\.?|કલમ)\s*([0-9૦૧૨૩૪૫૬૭૮૯]{1,4}[A-Za-z]?)", re.I),
    "named person": re.compile(r"\b(?:Person|Accused|Witness|Complainant|Victim)\s+[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})?\b"),
    "location": re.compile(r"\b(?:at|near|in|from|to)\s+([A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,}){0,3})"),
}


def _canonical_value(field: str, value: str) -> str:
    """Compare equivalent source spellings without hiding the source span."""
    if field == "date":
        return normalize_date(value) or value.translate(GUJARATI_DIGITS).replace(" ", "").upper()
    return value.translate(GUJARATI_DIGITS).replace(" ", "").upper()


def _citation(chunk: dict, label: str) -> dict:
    return {"document_id": chunk["document_id"], "page": chunk["page_number"],
            "chunk_id": chunk["id"], "label": label}


def _finding(kind: str, title: str, summary: str, sources: list[dict], differences: list[dict],
             roles: list[str], action: str, recommendation: str, questions: list[str]) -> dict:
    return {"id": f"finding_{uuid.uuid4().hex[:10]}", "type": kind, "title": title,
            "summary": summary, "classification": "REVIEW_REQUIRED", "confidence": 0.82,
            "supporting_sources": [], "contradicting_sources": sources, "entities": [],
            "factors": {"compared_documents": len({x.get("document_id") for x in sources}),
                        "difference_count": len(differences)}, "human_review_required": True,
            "verified": False, "issue": summary, "differences": differences,
            "why_important": "The inconsistency can affect the identity, reliability, or sequence of the prosecution case.",
            "recommended_correction": recommendation, "io_action": action,
            "defense_questions": questions, "related_document_roles": roles}


def comparative_findings(documents: list[dict], chunks: list[dict]) -> list[dict]:
    by_document = defaultdict(list)
    for chunk in chunks:
        by_document[chunk["document_id"]].append(chunk)
    doc_meta = {doc["id"]: doc for doc in documents}
    findings = []
    for field, pattern in FIELD_PATTERNS.items():
        values_by_doc = {}
        mentions = []
        for document_id, doc_chunks in by_document.items():
            values = set()
            for chunk in doc_chunks:
                values.update(_canonical_value(field, value) for value in pattern.findall(chunk["text"]))
                for value in pattern.findall(chunk["text"]):
                    mentions.append((value, chunk))
            if values:
                values_by_doc[document_id] = values
        all_values = set().union(*values_by_doc.values()) if values_by_doc else set()
        if len(all_values) < 2 or len(values_by_doc) < 2:
            continue
        relevant = [item for item in mentions if _canonical_value(field, item[0]) in all_values]
        sources = [_citation(chunk, f"{field.title()} mention — p{chunk['page_number']}") for _, chunk in relevant[:12]]
        differences = []
        for document_id, values in values_by_doc.items():
            doc = doc_meta.get(document_id, {})
            differences.append({"document": doc.get("filename", document_id),
                                "role": doc.get("role", "supporting_record"),
                                "value": ", ".join(sorted(values))})
        roles = sorted({doc_meta.get(document_id, {}).get("role", "supporting_record")
                        for document_id in values_by_doc})
        findings.append(_finding(
            "contradiction" if field in {"date", "time"} else "potential_mistake",
            f"Cross-document {field} discrepancy",
            f"Different {field} values were found across {len(values_by_doc)} source documents. The system cannot determine which value is correct.",
            sources, differences, roles,
            f"Compare the cited pages with the original record and document the correct {field} before filing.",
            f"Confirm the correct {field}, then correct every affected document or explain the discrepancy in the case record.",
            [f"Which document is the source for the disputed {field}?",
             f"Why does the charge sheet use a different {field} from the other record?"]
        ))
    return findings


def completeness_findings(documents: list[dict], chunks: list[dict]) -> list[dict]:
    present = {doc.get("role") for doc in documents}
    if "draft_chargesheet" not in present:
        return []
    required = {"fir": "FIR", "witness_statement": "witness statement", "medical_report": "medical report",
                "forensic_report": "forensic report", "seizure_memo": "seizure memo"}
    findings = []
    for role, label in required.items():
        if role in present:
            continue
        findings.append(_finding(
            "missing_link", f"No {label} was uploaded for comparison",
            f"The case contains a draft chargesheet but no uploaded document identified as a {label}.", [], [], ["draft_chargesheet", role],
            f"Confirm whether the {label} exists and upload it or record why it is unavailable.",
            f"Add the {label} to the filing set, or explicitly explain its absence in the case diary and filing review.",
            [f"Can the prosecution produce the {label} if challenged?", f"Why is the {label} absent from the filing set?"]
        ))
    return findings


def custody_findings(documents: list[dict], chunks: list[dict]) -> list[dict]:
    custody_terms = re.compile(r"chain[- ]of[- ]custody|sealed|seal number|malkhana|exhibit|hash|handed over|received", re.I)
    evidence_chunks = [chunk for chunk in chunks if custody_terms.search(chunk["text"])]
    if not evidence_chunks:
        return []
    weak = [chunk for chunk in evidence_chunks if not re.search(r"date|time|seal|hash|received|handed over", chunk["text"], re.I)]
    if not weak:
        return []
    sources = [_citation(chunk, f"Custody reference — p{chunk['page_number']}") for chunk in weak[:8]]
    return [_finding("missing_link", "Chain-of-custody details require verification",
                     "Evidence custody language is present, but the cited passage does not contain enough linked transfer, seal, or receipt detail for automatic confirmation.",
                     sources, [], ["supporting_record"],
                     "Verify seizure, sealing, storage, transfer, receipt, and laboratory records against the exhibit identifier.",
                     "Attach or cross-reference the complete chain-of-custody record and resolve any missing transfer interval.",
                     ["Who possessed the exhibit during the unaccounted interval?", "Where is the seal or receipt record?"])]
