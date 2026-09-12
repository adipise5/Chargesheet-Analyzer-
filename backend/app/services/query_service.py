from __future__ import annotations

from pathlib import Path

from app.graph.repository import graph_repository
from app.rag.context_builder import build_context
from app.rag.hybrid_retriever import HybridRetriever
from app.services.ollama_service import OllamaService
from app.storage.sqlite import db


def query_case(case_id: str, question: str) -> dict:
    chunks = db.all("SELECT c.*,d.filename AS document_label FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.case_id=?", (case_id,))
    graph = graph_repository.data(case_id)
    results = HybridRetriever().retrieve(question, graph, chunks)
    context, citations = build_context(results)
    if not citations:
        return {"answer": "Insufficient information: no relevant source passage was located in the uploaded record.",
                "citations": [], "graph_paths": [], "confidence": 0.0, "review_required": True, "retrieval": []}
    prompt_text = (Path(__file__).parents[1] / "prompts" / "graph_rag_answer.txt").read_text()
    prompt = f"{prompt_text}\n\nQUESTION:\n{question}\n\nRETRIEVED LOCAL CONTEXT:\n{context}"
    try:
        answer = OllamaService().answer(prompt)
        review_required = False
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

