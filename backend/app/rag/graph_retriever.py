from __future__ import annotations

from app.rag.lexical_retriever import tokens


class GraphRetriever:
    def retrieve(self, question: str, graph: dict, chunks: list[dict], limit: int = 12) -> list[dict]:
        query_tokens = set(tokens(question))
        seeds = {node["id"] for node in graph["nodes"] if query_tokens & set(tokens(node["label"]))}
        if not seeds:
            return []
        expanded = set(seeds)
        paths: dict[str, list[str]] = {seed: [seed] for seed in seeds}
        for edge in graph["edges"]:
            if edge["source"] in seeds:
                expanded.add(edge["target"]); paths[edge["target"]] = [edge["source"], edge["target"]]
            if edge["target"] in seeds:
                expanded.add(edge["source"]); paths[edge["source"]] = [edge["target"], edge["source"]]
        chunk_ids = set()
        for edge in graph["edges"]:
            if edge["source"] in expanded and edge["target"].startswith("chunk_"):
                chunk_ids.add(edge["target"])
            if edge["target"] in expanded and edge["source"].startswith("chunk_"):
                chunk_ids.add(edge["source"])
            for citation in edge.get("citations", []):
                if edge["source"] in expanded or edge["target"] in expanded:
                    chunk_ids.add(citation["chunk_id"])
        return [{**chunk, "score": 1.0, "retrieval_method": "graph", "graph_neighbors": list(expanded)}
                for chunk in chunks if chunk["id"] in chunk_ids][:limit]

