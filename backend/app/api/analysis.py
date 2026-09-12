from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query

from app.agents.summary_agent import case_summary, summary_fingerprint, summary_source_text
from app.graph.repository import graph_repository
from app.extraction.date_utils import normalize_date
from app.services.analysis_service import get_findings
from app.services.case_service import get_case
from app.storage.sqlite import db

router = APIRouter(prefix="/api/cases/{case_id}", tags=["analysis"])


def _assert_case(case_id: str) -> dict:
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@router.get("/overview")
def overview(case_id: str):
    case = _assert_case(case_id)
    objects = db.all("SELECT kind,COUNT(*) count FROM objects WHERE case_id=? GROUP BY kind", (case_id,))
    object_counts = {row["kind"]: row["count"] for row in objects}
    metrics = {
        "pages": db.one("SELECT COUNT(*) count FROM pages WHERE case_id=?", (case_id,))["count"],
        "accused": object_counts.get("Accused", 0), "witnesses": object_counts.get("Witness", 0),
        "evidence": sum(object_counts.get(kind, 0) for kind in ("Evidence", "DigitalEvidence", "PhysicalEvidence", "ForensicEvidence")),
        "claims": object_counts.get("Claim", 0),
        "contradictions": db.one("SELECT COUNT(*) count FROM findings WHERE case_id=? AND type='contradiction'", (case_id,))["count"],
        "review_flags": db.one("SELECT COUNT(*) count FROM pages WHERE case_id=? AND review_status='needs_review'", (case_id,))["count"] +
                        db.one("SELECT COUNT(*) count FROM findings WHERE case_id=? AND json_extract(data_json,'$.human_review_required')=1", (case_id,))["count"],
    }
    summary_counts = {"documents": db.one("SELECT COUNT(*) count FROM documents WHERE case_id=?", (case_id,))["count"],
                      **metrics}
    graph = graph_repository.data(case_id)
    source_text = summary_source_text(case_id, db)
    important = [node for node in graph["nodes"] if node["type"] in {"Accused", "Witness", "Evidence", "Event"}][:8]
    documents = db.all("SELECT id,sha256,role,category,page_count FROM documents WHERE case_id=? ORDER BY id", (case_id,))
    fingerprint = summary_fingerprint(case, summary_counts, source_text, documents)
    cached = db.one("SELECT summary_json FROM cases WHERE id=? AND summary_fingerprint=?", (case_id, fingerprint))
    summary_cached = False
    summary = None
    if cached and cached.get("summary_json"):
        try:
            candidate = json.loads(cached["summary_json"])
            if isinstance(candidate, dict) and isinstance(candidate.get("english"), str) and isinstance(candidate.get("gujarati"), str):
                summary = candidate
                summary_cached = True
        except (TypeError, json.JSONDecodeError):
            summary = None
    if summary is None:
        summary = case_summary(case, summary_counts, source_text)
        db.execute("UPDATE cases SET summary_json=?,summary_fingerprint=? WHERE id=?", (json.dumps(summary, ensure_ascii=False), fingerprint, case_id))
    return {"case": case, "metrics": metrics, "summary": summary, "summary_cached": summary_cached,
            "key_entities": important, "priority_findings": get_findings(case_id)[:4]}


@router.get("/findings")
def findings(case_id: str, type: str | None = Query(default=None)):
    _assert_case(case_id)
    return get_findings(case_id, type)


@router.get("/defense")
def defense(case_id: str):
    """Return review findings framed as possible defense challenges."""
    _assert_case(case_id)
    result = []
    for item in get_findings(case_id):
        if item.get("type") == "strong_point":
            continue
        result.append({"id": item["id"], "type": item["type"], "title": item["title"],
                       "weakness": item.get("issue") or item["summary"],
                       "defense_questions": item.get("defense_questions", []),
                       "relevant_sources": item.get("supporting_sources", []) + item.get("contradicting_sources", []),
                       "io_action": item.get("io_action", "Review the cited source pages and record the explanation."),
                       "recommended_correction": item.get("recommended_correction", ""),
                       "why_important": item.get("why_important", ""), "differences": item.get("differences", []),
                       "confidence": item.get("confidence", 0), "review_required": True})
    return result


@router.get("/evidence")
def evidence(case_id: str):
    _assert_case(case_id)
    graph = graph_repository.data(case_id)
    evidence_types = {"Evidence", "DigitalEvidence", "PhysicalEvidence", "ForensicEvidence"}
    result = []
    for node in graph["nodes"]:
        if node["type"] not in evidence_types:
            continue
        linked = [edge for edge in graph["edges"] if edge["source"] == node["id"] or edge["target"] == node["id"]]
        citations = [citation for edge in linked for citation in edge.get("citations", [])]
        result.append({"id": node["id"], "type": node["metadata"].get("subtype", node["type"]),
                       "label": node["label"], "confidence": node["confidence"], "citations": citations,
                       "linked_claims": [edge["target"] for edge in linked if edge["relation"] in {"SUPPORTS", "CONTRADICTS"}],
                       "verification": "verified" if any(edge["human_verified"] for edge in linked) else "machine_extracted"})
    return result


@router.get("/timeline")
def timeline(case_id: str):
    _assert_case(case_id)
    graph = graph_repository.data(case_id)
    results = []
    for node in graph["nodes"]:
        if node["type"] != "Event":
            continue
        edges = [edge for edge in graph["edges"] if edge["source"] == node["id"] or edge["target"] == node["id"]]
        citations = [c for e in edges for c in e.get("citations", [])]
        raw_date = node["metadata"].get("date")
        results.append({"id": node["id"], "date": node["metadata"].get("normalized_date") or normalize_date(raw_date) or raw_date, "time": node["metadata"].get("time"),
                        "event": node["label"], "people": [], "location": "Training Square" if "Training" in node["label"] else None,
                        "category": node["metadata"].get("subtype", "investigation"), "confidence": node["confidence"],
                        "uncertain": node["confidence"] < .8, "citation": citations[0] if citations else None})
    return results

