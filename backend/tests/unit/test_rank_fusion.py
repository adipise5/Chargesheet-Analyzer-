from app.rag.hybrid_retriever import reciprocal_rank_fusion


def row(identifier, method):
    return {"id": identifier, "retrieval_method": method, "score": 1, "text": identifier}


def test_rrf_rewards_multiple_retrieval_methods():
    result = reciprocal_rank_fusion([[row("a", "graph"), row("b", "graph")], [row("b", "lexical")]])
    assert result[0]["id"] == "b"
    assert set(result[0]["methods"]) == {"graph", "lexical"}

