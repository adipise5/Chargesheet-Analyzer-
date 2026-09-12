from __future__ import annotations

import json

from app.graph.vector_index import cosine_similarity
from app.services.embedding_service import OllamaEmbeddingProvider


class SemanticRetriever:
    def __init__(self, provider=None):
        self.provider = provider or OllamaEmbeddingProvider()

    def retrieve(self, question: str, chunks: list[dict], limit: int = 12) -> list[dict]:
        available = [chunk for chunk in chunks if chunk.get("embedding_json")]
        if not available:
            return []
        vector = self.provider.embed([question])[0]
        results = []
        for chunk in available:
            score = cosine_similarity(vector, json.loads(chunk["embedding_json"]))
            results.append({**chunk, "score": score, "retrieval_method": "semantic"})
        return sorted(results, key=lambda row: row["score"], reverse=True)[:limit]

