from app.api import analysis


def test_timeline_is_returned_in_chronological_order(monkeypatch):
    monkeypatch.setattr(analysis, "get_case", lambda _: {"id": "case-1"})
    monkeypatch.setattr(analysis.graph_repository, "data", lambda _: {
        "nodes": [
            {"id": "late", "type": "Event", "label": "Later", "metadata": {"normalized_date": "2026-03-20"}, "confidence": .9},
            {"id": "early", "type": "Event", "label": "Earlier", "metadata": {"normalized_date": "2026-03-10"}, "confidence": .9},
        ], "edges": [],
    })
    assert [item["id"] for item in analysis.timeline("case-1")] == ["early", "late"]
