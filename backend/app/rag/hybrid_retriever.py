from __future__ import annotations

from app.core.runtime_mode import is_read_only_demo

from .graph_retriever import GraphRetriever
from .lexical_retriever import LexicalRetriever
from .semantic_retriever import SemanticRetriever


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60, limit: int = 12) -> list[dict]:
    fused: dict[str, dict] = {}
    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            record = fused.setdefault(item["id"], {**item, "rrf_score": 0.0, "methods": []})
            record["rrf_score"] += 1 / (k + rank)
            if item["retrieval_method"] not in record["methods"]:
                record["methods"].append(item["retrieval_method"])
    return sorted(fused.values(), key=lambda row: row["rrf_score"], reverse=True)[:limit]


class HybridRetriever:
    def __init__(self):
        self.lexical = LexicalRetriever()
        self.graph = GraphRetriever()
        self.semantic = None if is_read_only_demo() else SemanticRetriever()

    def retrieve(self, question: str, graph: dict, chunks: list[dict], limit: int = 12) -> list[dict]:
        lists = [self.graph.retrieve(question, graph, chunks), self.lexical.retrieve(question, chunks)]
        if self.semantic is not None and not is_read_only_demo():
            try:
                lists.append(self.semantic.retrieve(question, chunks))
            except Exception:
                # Local model readiness is returned in API system status; no remote fallback is attempted.
                pass
        return reciprocal_rank_fusion(lists, limit=limit)

