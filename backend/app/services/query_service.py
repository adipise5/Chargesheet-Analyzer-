from __future__ import annotations

from pathlib import Path

from app.graph.repository import graph_repository
from app.rag.context_builder import build_context
from app.rag.hybrid_retriever import HybridRetriever
from app.services.ollama_service import OllamaService
from app.storage.sqlite import db


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


def query_case(case_id: str, question: str) -> dict:
    chunks = db.all("SELECT c.*,d.filename AS document_label FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.case_id=?", (case_id,))
    graph = graph_repository.data(case_id)
    normalized_question = question.lower()
    if "evidence" in normalized_question and ("unlinked" in normalized_question or "not linked" in normalized_question):
        deterministic = _unlinked_evidence_response(graph)
        if deterministic:
            db.audit("question_asked", case_id, {"count": 1})
            db.audit("sources_retrieved", case_id, {"count": len(deterministic["citations"])})
            return deterministic
    results = HybridRetriever().retrieve(question, graph, chunks)
    context, citations = build_context(results)
    if not citations:
        return {"answer": "Insufficient information: no relevant source passage was located in the uploaded record.",
                "citations": [], "graph_paths": [], "confidence": 0.0, "review_required": True, "retrieval": []}
    prompt_text = (Path(__file__).parents[1] / "prompts" / "graph_rag_answer.txt").read_text()
    prompt = f"{prompt_text}\n\nQUESTION:\n{question}\n\nRETRIEVED LOCAL CONTEXT:\n{context}"
    try:
        answer = OllamaService().answer(prompt)
        review_required = True
        confidence = min(0.9, 0.58 + 0.04 * len(citations))
    except Exception:
        excerpts = []
        for item in results[:3]:
            compact = " ".join(item["text"].split())[:260]
            excerpts.append(f"• {compact} [{item.get('document_label', 'Document')} p.{item['page_number']}]")
        answer = ("The following relevant source passages were located in the uploaded record. The local Qwen model is unavailable, "
                  "so no synthesized conclusion has been generated:\n" + "\n".join(excerpts))
        review_required = True
        confidence = 0.55
    db.audit("question_asked", case_id, {"count": 1})
    db.audit("sources_retrieved", case_id, {"count": len(citations)})
    return {"answer": answer, "citations": citations, "graph_paths": [], "confidence": confidence,
            "review_required": review_required,
            "retrieval": [{"chunk_id": r["id"], "method": r["methods"], "score": r["rrf_score"],
                           "document_id": r["document_id"], "page": r["page_number"]} for r in results]}

