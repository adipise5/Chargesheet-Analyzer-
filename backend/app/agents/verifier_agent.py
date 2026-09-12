from __future__ import annotations

from app.graph.provenance import citations_are_valid


def verify_findings(findings: list[dict], known_chunks: set[str]) -> list[dict]:
    verified = []
    for finding in findings:
        citations = finding.get("supporting_sources", []) + finding.get("contradicting_sources", [])
        finding["verified"] = citations_are_valid(citations, known_chunks)
        if not finding["verified"]:
            finding["human_review_required"] = True
            finding["classification"] = "REVIEW_REQUIRED"
        verified.append(finding)
    return verified

