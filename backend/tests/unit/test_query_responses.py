from app.rag.context_builder import build_context
from app.services.ollama_service import LocalModelUnavailable, OllamaService
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
