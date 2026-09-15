import json

from app.api import system
from app.services import judgment_service
from app.services.case_service import create_case
from app.storage.sqlite import db


def test_precedent_insight_is_reused_until_case_or_corpus_changes(monkeypatch):
    case = create_case({"case_number": "PRECEDENT-CACHE", "police_station": "Training"})
    db.execute(
        "INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
        ("finding-cache", case["id"], "weak_point", json.dumps({"summary": "witness evidence contradiction"})),
    )
    db.execute(
        "INSERT INTO judgments(id,title,court,judgment_year,filename,stored_path,page_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
        ("judgment-cache", "Synthetic judgment", "Training Court", "2026", "judgment.pdf", "", 1, "2026-01-01"),
    )
    db.execute(
        "INSERT INTO judgment_chunks(id,judgment_id,page_number,text,normalized_text) VALUES(?,?,?,?,?)",
        ("jchunk-cache", "judgment-cache", 1, "The witness evidence contradiction required careful investigation.", ""),
    )
    calls = []

    class FakeOllama:
        def answer(self, prompt):
            calls.append(prompt)
            return "Cached precedent insight"

    monkeypatch.setattr(judgment_service, "OllamaService", FakeOllama)
    first = judgment_service.analyze_precedents(case["id"])
    second = judgment_service.analyze_precedents(case["id"])

    assert first == second
    assert len(calls) == 1


def test_translation_is_reused_and_english_source_skips_model(monkeypatch):
    calls = []

    class FakeOllama:
        def answer(self, prompt):
            calls.append(prompt)
            return '["English translation"]'

    monkeypatch.setattr("app.services.ollama_service.OllamaService", FakeOllama)
    payload = system.TranslationRequest(texts=["ગુજરાતી લખાણ"], target="english")
    first = system.translate(payload)
    second = system.translate(payload)
    identity = system.translate(system.TranslationRequest(texts=["Already English"], target="english"))

    assert first["translations"] == ["English translation"]
    assert second["translations"] == ["English translation"]
    assert identity["translations"] == ["Already English"]
    assert len(calls) == 1


def test_translation_parser_accepts_qwen_nested_array_without_rendering_source(monkeypatch):
    class FakeOllama:
        def answer(self, prompt):
            return '[["આ કેસમાં કોઈ ભૌતિક પુરાવા નથી."], "This case has no physical evidence."]'

    monkeypatch.setattr("app.services.ollama_service.OllamaService", FakeOllama)
    result = system.translate(system.TranslationRequest(
        texts=["This case has no physical evidence."], target="gujarati"
    ))

    assert result["translations"] == ["આ કેસમાં કોઈ ભૌતિક પુરાવા નથી."]
