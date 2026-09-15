from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.core.config import settings
from app.graph.repository import graph_repository
from app.rag.context_builder import build_context
from app.rag.hybrid_retriever import HybridRetriever
from app.services.analysis_service import get_findings
from app.services.ollama_service import OllamaService
from app.storage.sqlite import db, now_iso


def _unlinked_evidence_response(graph: dict) -> dict | None:
    """Answer the UI's unlinked-evidence question from graph facts, not synthesis."""
    evidence_types = {"Evidence", "DigitalEvidence", "PhysicalEvidence", "ForensicEvidence"}
    unlinked: list[tuple[dict, list[dict]]] = []
    for node in graph["nodes"]:
        if node["type"] not in evidence_types:
            continue
        edges = [edge for edge in graph["edges"] if edge["source"] == node["id"] or edge["target"] == node["id"]]
        linked_to_claim = any(
            edge["relation"] in {"SUPPORTS", "CONTRADICTS"}
            and any(candidate["id"] in {edge["source"], edge["target"]} and candidate["type"] == "Claim" for candidate in graph["nodes"])
            for edge in edges
        )
        if not linked_to_claim:
            unlinked.append((node, [citation for edge in edges for citation in edge.get("citations", [])]))
    if not unlinked:
        return None
    citations: list[dict] = []
    seen = set()
    lines = ["The following evidence nodes are not linked to a claim in the current extracted graph:"]
    for node, sources in unlinked[:12]:
        label = sources[0].get("label", "source passage") if sources else "no source citation"
        lines.append(f"• {node['label']} — {label}.")
        for citation in sources:
            key = (citation.get("document_id"), citation.get("page"), citation.get("chunk_id"))
            if key not in seen:
                seen.add(key)
                citations.append(citation)
    if len(unlinked) > 12:
        lines.append(f"• {len(unlinked) - 12} additional extracted evidence node(s) are also unlinked.")
    return {"answer": "\n".join(lines), "citations": citations, "graph_paths": [], "confidence": 0.8,
            "review_required": True, "retrieval": []}


def _single_source_response(case_id: str) -> dict:
    findings = [item for item in get_findings(case_id) if item.get("type") == "weak_point" and len(item.get("supporting_sources", [])) == 1]
    if not findings:
        return {"answer": "No claim currently has a stored single-source weakness finding. This does not prove corroboration; review the source-linked findings and original records.",
                "citations": [], "graph_paths": [], "confidence": 0.85, "review_required": True, "retrieval": []}
    citations, seen, lines = [], set(), ["Stored analysis identifies these claims as relying on one source passage:"]
    for finding in findings[:12]:
        source = finding["supporting_sources"][0]
        lines.append(f"• {finding.get('title', 'Extracted claim')} — verify independent corroboration.")
        key = (source.get("document_id"), source.get("page"), source.get("chunk_id"))
        if key not in seen:
            seen.add(key)
            citations.append(source)
    return {"answer": "\n".join(lines), "citations": citations, "graph_paths": [], "confidence": 0.9,
            "review_required": True, "retrieval": []}


def _overview_response(case_id: str, chunks: list[dict]) -> dict | None:
    row = db.one("SELECT summary_json FROM cases WHERE id=?", (case_id,))
    if not row or not row.get("summary_json"):
        return None
    try:
        summary = json.loads(row["summary_json"])
    except (TypeError, json.JSONDecodeError):
        return None
    answer = summary.get("english")
    if not isinstance(answer, str) or not answer.strip():
        return None
    citations = [{"document_id": item["document_id"], "page": item["page_number"],
                  "chunk_id": item["id"], "label": f"{index + 1}: {item.get('document_label', 'Document')}"}
                 for index, item in enumerate(chunks[:4])]
    return {"answer": answer, "citations": citations, "graph_paths": [], "confidence": 0.75,
            "review_required": True, "retrieval": []}


def _filing_checklist_response(case_id: str) -> dict:
    findings = [item for item in get_findings(case_id) if item.get("type") != "strong_point"]
    if not findings:
        return {"answer": "No stored review findings are available yet. Confirm that the case has finished processing and inspect the original records before filing.",
                "citations": [], "graph_paths": [], "confidence": 0.35, "review_required": True, "retrieval": []}
    citations, seen, lines = [], set(), ["Before filing, review these stored issues and record how each was resolved:"]
    for finding in findings[:8]:
        action = finding.get("io_action") or finding.get("recommended_correction") or "Review the cited source pages."
        lines.append(f"• {finding.get('title', 'Review item')}: {action}")
        for citation in (finding.get("supporting_sources") or []) + (finding.get("contradicting_sources") or []):
            key = (citation.get("document_id"), citation.get("page"), citation.get("chunk_id"))
            if key not in seen:
                seen.add(key)
                citations.append(citation)
    return {"answer": "\n".join(lines), "citations": citations[:12], "graph_paths": [], "confidence": 0.9,
            "review_required": True, "retrieval": []}


def _extractive_response(results: list[dict], *, hosted: bool = False) -> str:
    if hosted:
        lead = "This read-only demo is using its precomputed/source-only answer path; no live model inference runs on Render. Relevant source passages:"
    else:
        lead = "Relevant source passages were located, but no synthesized conclusion was generated because the local Qwen model is unavailable:"
    excerpts = []
    for item in results[:4]:
        compact = " ".join(item["text"].split())[:320]
        excerpts.append(f"• {compact} [{item.get('document_label', 'Document')} p.{item['page_number']}]")
    return lead + "\n" + "\n".join(excerpts)


def _source_fingerprint(chunks: list[dict]) -> str:
    payload = [{key: item.get(key) for key in ("id", "document_id", "page_number", "text")}
               for item in chunks]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _question_key(question: str) -> str:
    normalized = " ".join(question.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _cached_response(case_id: str, question: str, source_fingerprint: str) -> dict | None:
    row = db.one("SELECT * FROM query_cache WHERE case_id=? AND question_key=? AND source_fingerprint=?",
                 (case_id, _question_key(question), source_fingerprint))
    if not row:
        return None
    try:
        return {"answer": row["answer"], "citations": json.loads(row["citations_json"]),
                "graph_paths": [], "confidence": row["confidence"],
                "review_required": bool(row["review_required"]), "retrieval": json.loads(row["retrieval_json"])}
    except (TypeError, json.JSONDecodeError, KeyError):
        return None


def _store_response(case_id: str, question: str, source_fingerprint: str, response: dict) -> None:
    db.execute(
        "INSERT INTO query_cache(id,case_id,question_key,question,source_fingerprint,answer,citations_json,retrieval_json,confidence,review_required,created_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(case_id,question_key,source_fingerprint) DO UPDATE SET answer=excluded.answer,citations_json=excluded.citations_json,retrieval_json=excluded.retrieval_json,confidence=excluded.confidence,review_required=excluded.review_required,created_at=excluded.created_at",
        (f"query_{hashlib.sha256((case_id + source_fingerprint + question).encode('utf-8')).hexdigest()}",
         case_id, _question_key(question), question[:1000], source_fingerprint, response["answer"],
         json.dumps(response.get("citations", []), ensure_ascii=False),
         json.dumps(response.get("retrieval", []), ensure_ascii=False), response.get("confidence", 0),
         int(response.get("review_required", True)), now_iso()),
    )


def _guard_unsupported_section_labels(answer: str, source_text: str, question: str) -> str:
    """Remove common model hallucinations such as ``302 (Murder)``.

    A source can establish that a number was written in a record, but not the
    legal meaning of that number. The prompt states this explicitly; this
    small post-generation guard protects the UI when a local model ignores it.
    """
    if not re.search(r"\b(section|sections|ipc|bns|offen[cs]e|law|act|કલમ)\b", question, re.I):
        return answer
    source_numbers = {match.group(0) for match in re.finditer(r"(?<!\w)\d{1,4}[A-Za-z]?(?!\w)", source_text)}
    changed = False
    guarded = answer
    for number in sorted(source_numbers, key=len, reverse=True):
        pattern = re.compile(rf"(?<!\w){re.escape(number)}\s*\(([^)\n]{{2,90}})\)", re.I)

        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            label = match.group(1).strip()
            if label.casefold() in source_text.casefold():
                return match.group(0)
            changed = True
            return number

        guarded = pattern.sub(replace, guarded)
    if changed and "meaning" not in guarded.casefold():
        guarded += "\n\nThe uploaded record lists section numbers but does not establish their legal meanings; verify the authoritative statutory text separately."
    return guarded


def query_case(case_id: str, question: str, *, persist: bool = False) -> dict:
    chunks = db.all("SELECT c.*,d.filename AS document_label FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.case_id=?", (case_id,))
    source_fingerprint = _source_fingerprint(chunks)
    if settings.render_demo or persist:
        cached = _cached_response(case_id, question, source_fingerprint)
        if cached:
            return cached
    graph = graph_repository.data(case_id)
    normalized_question = question.casefold()
    if "single source" in normalized_question or "only one source" in normalized_question or "one source" in normalized_question:
        response = _single_source_response(case_id)
    elif "evidence" in normalized_question and ("unlinked" in normalized_question or "not linked" in normalized_question):
        response = _unlinked_evidence_response(graph)
        if response is None:
            response = {"answer": "No extracted evidence node is currently unlinked from a claim. This graph result is not proof that all evidence is complete or admissible.",
                        "citations": [], "graph_paths": [], "confidence": 0.8, "review_required": True, "retrieval": []}
    elif any(phrase in normalized_question for phrase in ("what is this case about", "case summary", "summarize this case", "summarise this case")):
        response = _overview_response(case_id, chunks)
        if response is None:
            response = {"answer": "A cached case summary is not available yet. Review the Overview and source documents after processing completes.",
                        "citations": [], "graph_paths": [], "confidence": 0.35, "review_required": True, "retrieval": []}
    elif ("verify" in normalized_question or "check" in normalized_question) and ("fil" in normalized_question or "charge sheet" in normalized_question or "chargesheet" in normalized_question):
        response = _filing_checklist_response(case_id)
    else:
        results = HybridRetriever().retrieve(question, graph, chunks)
        context, citations = build_context(results)
        retrieval = [{"chunk_id": r["id"], "method": r["methods"], "score": r["rrf_score"],
                      "document_id": r["document_id"], "page": r["page_number"]} for r in results]
        if not citations:
            response = {"answer": "Insufficient information: no relevant source passage was located in the uploaded record.",
                        "citations": [], "graph_paths": [], "confidence": 0.0, "review_required": True, "retrieval": []}
        elif settings.render_demo:
            response = {"answer": _extractive_response(results, hosted=True), "citations": citations,
                        "graph_paths": [], "confidence": 0.55, "review_required": True, "retrieval": retrieval}
        else:
            prompt_text = (Path(__file__).parents[1] / "prompts" / "graph_rag_answer.txt").read_text()
            prompt = f"{prompt_text}\n\nQUESTION:\n{question}\n\nRETRIEVED LOCAL CONTEXT:\n{context}"
            try:
                service = OllamaService()
                bounded = getattr(service, "answer_bounded", None)
                answer = bounded(prompt) if bounded else service.answer(prompt)
                answer = _guard_unsupported_section_labels(answer, "\n".join(item["text"] for item in results), question)
                response = {"answer": answer, "citations": citations, "graph_paths": [],
                            "confidence": min(0.9, 0.58 + 0.04 * len(citations)), "review_required": True,
                            "retrieval": retrieval}
            except Exception:
                response = {"answer": _extractive_response(results), "citations": citations, "graph_paths": [],
                            "confidence": 0.55, "review_required": True, "retrieval": retrieval}
    if persist:
        _store_response(case_id, question, source_fingerprint, response)
    db.audit("question_asked", case_id, {"count": 1})
    db.audit("sources_retrieved", case_id, {"count": len(response.get("citations", []))})
    return response
