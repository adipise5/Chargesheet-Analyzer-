from app.rag.context_builder import build_context
from app.services.ollama_service import LocalModelUnavailable, OllamaService
from app.services.query_service import query_case
from app.storage.sqlite import db
import json
import pytest


def test_short_citations_keep_exact_page_and_chunk_provenance():
    context, citations = build_context([
        {"id": "chunk-1", "document_id": "doc-1", "page_number": 3,
         "text": "A witness described the vehicle.", "document_label": "record.pdf"},
        {"id": "chunk-2", "document_id": "doc-1", "page_number": 4,
         "text": "The next page records a different time.", "document_label": "record.pdf"},
    ])
    assert "[S1]" in context and "[S2]" in context
    assert "chunk-1" not in context
    assert citations[0] == {"document_id": "doc-1", "page": 3,
                            "chunk_id": "chunk-1", "label": "S1: record.pdf"}
    assert citations[1]["page"] == 4


@pytest.mark.parametrize("content,reason", [("", "stop"), ("Partial answer", "length")])
def test_model_empty_and_truncated_answers_are_not_silent(monkeypatch, content, reason):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": content}, "done_reason": reason}

    class Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("app.services.ollama_service.httpx.Client", Client)
    if not content:
        with pytest.raises(LocalModelUnavailable):
            OllamaService().answer("Summarize the case")
    else:
        assert "response limit" in OllamaService().answer("Summarize the case")


def test_single_source_question_uses_stored_findings_without_model(monkeypatch):
    db.execute("INSERT INTO cases(id,case_number,police_station,language,status,is_demo,created_at,updated_at) VALUES(?,?,?,?,?,0,datetime('now'),datetime('now'))",
               ("case-1", "TEST-1", "Test", "English", "ready"))
    finding = {"id": "finding-1", "type": "weak_point", "title": "Claim needing corroboration",
               "summary": "This candidate claim is presently linked to a single source passage.",
               "supporting_sources": [{"document_id": "doc-1", "page": 2, "chunk_id": "chunk-1", "label": "S1: record.pdf"}]}
    db.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
               ("finding-1", "case-1", "weak_point", json.dumps(finding)))
    monkeypatch.setattr("app.services.query_service.OllamaService.answer", lambda *_: pytest.fail("model should not run"))
    response = query_case("case-1", "Which claims rely on only one source?")
    assert "Claim needing corroboration" in response["answer"]
    assert response["citations"][0]["page"] == 2
