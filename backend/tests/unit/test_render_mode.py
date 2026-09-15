import json

from fastapi.testclient import TestClient

from app.rag.hybrid_retriever import HybridRetriever
from app.main import app
from app.services.query_service import _guard_unsupported_section_labels, query_case
from app.storage.sqlite import db


def test_legal_section_guard_does_not_allow_model_to_define_a_number():
    source = "The report lists IPC sections 300, 302 and 349."
    answer = "The report lists IPC 300 (Carnage) and 302 (Murder)."
    guarded = _guard_unsupported_section_labels(answer, source, "Which offences and sections are listed?")
    assert "300 (Carnage)" not in guarded
    assert "302 (Murder)" not in guarded
    assert "IPC 300" in guarded and "302" in guarded
    assert "does not establish their legal meanings" in guarded


def test_persisted_demo_answer_is_reused_without_saving_interactive_chat(monkeypatch):
    db.execute("INSERT INTO cases(id,case_number,police_station,language,status,is_demo,created_at,updated_at) VALUES(?,?,?,?,?,0,datetime('now'),datetime('now'))",
               ("case-render-cache", "RENDER-CACHE", "Training", "English", "ready"))
    db.execute("INSERT INTO documents(id,case_id,filename,stored_name,category,page_count,sha256,status,role,created_at) VALUES(?,?,?,?,?,?,?,?,?,datetime('now'))",
               ("doc-render-cache", "case-render-cache", "public.pdf", "doc-render-cache.pdf", "chargesheet", 1, "render-cache-digest", "processed", "draft_chargesheet"))
    db.execute("INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
               ("chunk-render-cache", "case-render-cache", "doc-render-cache", 1, "Public record says a fictional event occurred.", "public record", "english", "{}"))
    db.execute("UPDATE cases SET summary_json=? WHERE id=?",
               (json.dumps({"english": "A cached public demo summary.", "gujarati": "કેશ્ડ ડેમો સારાંશ."}), "case-render-cache"))
    first = query_case("case-render-cache", "What is this case about?", persist=True)
    monkeypatch.setenv("DEMO_SNAPSHOT_MODE", "true")
    second = query_case("case-render-cache", "What is this case about?")
    assert second == first
    assert db.one("SELECT COUNT(*) count FROM query_cache WHERE case_id=?", ("case-render-cache",))["count"] == 1


def test_render_api_is_read_only_and_skips_model_health(monkeypatch):
    monkeypatch.setenv("DEMO_SNAPSHOT_MODE", "true")
    monkeypatch.setattr("app.main.seed_snapshot", lambda *_: {})
    with TestClient(app) as client:
        health = client.get("/api/system/health")
        assert health.status_code == 200
        assert health.json()["read_only"] is True
        assert health.json()["models_required"] is False
        assert client.post("/api/cases", json={"case_number": "BLOCKED", "police_station": "Training", "language": "English"}).status_code == 403
        assert client.delete("/api/system/purge").status_code == 403


def test_render_retrieval_skips_semantic_model(monkeypatch):
    monkeypatch.setenv("DEMO_SNAPSHOT_MODE", "true")

    def fail(*_args, **_kwargs):
        raise AssertionError("hosted retrieval must not call the embedding model")

    monkeypatch.setattr("app.rag.hybrid_retriever.SemanticRetriever.retrieve", fail)
    chunks = [{"id": "chunk-1", "normalized_text": "public record event", "text": "Public record event.",
               "document_id": "doc-1", "page_number": 1, "document_label": "public.pdf"}]
    results = HybridRetriever().retrieve("public event", {"nodes": [], "edges": []}, chunks)
    assert results and results[0]["id"] == "chunk-1"
