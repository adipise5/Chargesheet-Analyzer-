from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.storage.sqlite import db
from app.services.case_service import create_case, delete_case, save_document


def test_major_demo_routes():
    with TestClient(app) as client:
        demo = client.post("/api/demo")
        assert demo.status_code == 200
        case_id = demo.json()["id"]
        for path in ("overview", "findings", "timeline", "evidence", "graph", "documents", "status"):
            response = client.get(f"/api/cases/{case_id}/{path}")
            assert response.status_code == 200, (path, response.text)
        answer = client.post(f"/api/cases/{case_id}/query", json={"question": "Which witnesses contain conflicting times?"})
        assert answer.status_code == 200
        assert answer.json()["citations"]


def test_rejects_external_model_url(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://external.example")
    with pytest.raises(ValueError, match="approved private address"):
        with TestClient(app):
            pass


def test_ocr_review_preserves_original_and_rebuilds():
    with TestClient(app) as client:
        case_id = client.post("/api/demo").json()["id"]
        db.execute("UPDATE pages SET review_status='needs_review' WHERE id='page_demo_2'")
        queue = client.get(f"/api/cases/{case_id}/ocr/review")
        assert queue.status_code == 200 and len(queue.json()) == 1
        original = queue.json()[0]["original_text"]
        corrected = original + "\nHuman reviewer confirmed this synthetic page."
        response = client.patch(f"/api/cases/{case_id}/ocr/review/page_demo_2",
                                json={"status": "human_corrected", "corrected_text": corrected})
        assert response.status_code == 200
        row = db.one("SELECT original_text,corrected_text,review_status FROM pages WHERE id='page_demo_2'")
        assert row["original_text"] == original
        assert row["corrected_text"] == corrected
        assert row["review_status"] == "human_corrected"


def test_delete_case_removes_database_rows_and_files(tmp_path, monkeypatch):
    import fitz
    from types import SimpleNamespace
    import app.services.case_service as case_service

    case_root = tmp_path / "cases"
    monkeypatch.setattr(case_service, "settings", SimpleNamespace(cases_dir=case_root, max_upload_bytes=250 * 1024 * 1024))
    case = create_case({"case_number": "DELETE-ME", "police_station": "Training"})
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((40, 40), "Synthetic disposable document")
    payload = pdf.tobytes()
    pdf.close()
    document = save_document(case["id"], "disposable.pdf", payload)
    stored = case_root / case["id"] / "documents" / f"{document['id']}.pdf"
    assert stored.exists()

    assert delete_case(case["id"])
    assert db.one("SELECT 1 FROM cases WHERE id=?", (case["id"],)) is None
    assert not stored.exists()


def test_purge_all_data_removes_runtime_rows_files_and_legacy_db(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import app.services.purge_service as purge_service
    from app.services.purge_service import TABLES

    cases_root = tmp_path / "cases"
    data_root = tmp_path / "data"
    cases_root.mkdir()
    (cases_root / ".gitkeep").write_text("")
    private_case_file = cases_root / "case_private" / "documents" / "private.pdf"
    private_case_file.parent.mkdir(parents=True)
    private_case_file.write_bytes(b"synthetic private test content")
    judgment_file = data_root / "legal_kb" / "judgments" / "judgment.pdf"
    judgment_file.parent.mkdir(parents=True)
    judgment_file.write_bytes(b"synthetic judgment")
    legacy_db = data_root / "chargesheet.sqlite"
    legacy_db.parent.mkdir(parents=True, exist_ok=True)
    legacy_db.write_bytes(b"legacy placeholder")
    monkeypatch.setattr(purge_service, "settings", SimpleNamespace(cases_dir=cases_root, data_dir=data_root))

    case = create_case({"case_number": "PURGE-ME", "police_station": "Synthetic Test"})
    db.execute("UPDATE cases SET summary_json=?,summary_fingerprint=?,precedents_json=?,precedents_fingerprint=? WHERE id=?",
               ('{"english":"synthetic","gujarati":"કૃત્રિમ"}', "summary-fingerprint", '{"insights":"synthetic"}', "precedent-fingerprint", case["id"]))
    db.execute("INSERT INTO documents(id,case_id,filename,stored_name,category,page_count,sha256,status,role,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
               ("doc_purge", case["id"], "private.pdf", "doc_purge.pdf", "fir", 1, "synthetic-digest", "processed", "fir", "2026-01-01"))
    db.execute("INSERT INTO pages(id,case_id,document_id,page_number,extraction_method,language,original_text,normalized_text,ocr_confidence,review_status,blocks_json,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
               ("page_purge", case["id"], "doc_purge", 1, "native_pdf", "english", "synthetic source", "synthetic source", 100, "accepted", "[]", "2026-01-01"))
    db.execute("INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
               ("chunk_purge", case["id"], "doc_purge", 1, "synthetic source", "synthetic source", "english", "{}"))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("object_purge", case["id"], "Claim", "claim", "synthetic claim", "{}", 1))
    db.execute("INSERT INTO relations(id,case_id,source_id,target_id,relation,confidence,citations_json,extraction_method,human_verified) VALUES(?,?,?,?,?,?,?,?,?)",
               ("relation_purge", case["id"], "object_purge", "chunk_purge", "PART_OF", 1, "[]", "test", 1))
    db.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
               ("finding_purge", case["id"], "weak_point", "{}"))
    db.execute("INSERT INTO jobs(id,case_id,state,stage,progress,counts_json,stages_json,error,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
               ("job_purge", case["id"], "complete", "done", 100, "{}", "[]", None, "2026-01-01"))
    db.execute("INSERT INTO audits(case_id,event,metadata_json,created_at) VALUES(?,?,?,?)",
               (case["id"], "synthetic_test", "{}", "2026-01-01"))
    db.execute("INSERT INTO judgments(id,title,court,judgment_year,filename,stored_path,page_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
               ("judgment_test", "Synthetic", "Test Court", "2026", "judgment.pdf", str(judgment_file), 1, "2026-01-01"))
    db.execute("INSERT INTO judgment_chunks(id,judgment_id,page_number,text,normalized_text) VALUES(?,?,?,?,?)",
               ("jchunk_purge", "judgment_test", 1, "synthetic judgment", "synthetic judgment"))
    db.execute("INSERT INTO translation_cache(text_hash,target,source_text,translated_text,created_at) VALUES(?,?,?,?,?)",
               ("translation-purge", "english", "કૃત્રિમ", "synthetic", "2026-01-01"))

    removed = purge_service.purge_all_data()

    assert removed["cases"] == 1
    assert removed["judgments"] == 1
    assert removed["translation_cache"] == 1
    assert db.one("SELECT 1 FROM cases WHERE id=?", (case["id"],)) is None
    assert db.one("SELECT 1 FROM judgments WHERE id='judgment_test'") is None
    for table in TABLES:
        assert db.one(f"SELECT COUNT(*) count FROM {table}")["count"] == 0
    assert list(cases_root.iterdir()) == [cases_root / ".gitkeep"]
    assert not judgment_file.exists()
    assert not legacy_db.exists()


def test_purge_endpoint_clears_data_and_keeps_api_usable(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import app.services.purge_service as purge_service

    cases_root = tmp_path / "cases"
    data_root = tmp_path / "data"
    cases_root.mkdir()
    (cases_root / ".gitkeep").write_text("")
    private_file = cases_root / "case_private" / "documents" / "private.pdf"
    private_file.parent.mkdir(parents=True)
    private_file.write_bytes(b"synthetic private content")
    monkeypatch.setattr(purge_service, "settings", SimpleNamespace(cases_dir=cases_root, data_dir=data_root))
    create_case({"case_number": "PURGE-ENDPOINT", "police_station": "Synthetic Test"})
    db.execute("INSERT INTO translation_cache(text_hash,target,source_text,translated_text,created_at) VALUES(?,?,?,?,?)",
               ("translation-endpoint", "english", "કૃત્રિમ", "synthetic", "2026-01-01"))

    with TestClient(app) as client:
        response = client.delete("/api/system/purge")
        assert response.status_code == 200
        assert response.json()["status"] == "purged"
        assert response.json()["removed"]["translation_cache"] == 1
        assert client.get("/api/cases").json() == []
        created = client.post("/api/cases", json={"case_number": "AFTER-PURGE", "police_station": "Training", "language": "English"})
        assert created.status_code == 201

    assert not private_file.exists()
    assert list(cases_root.iterdir()) == [cases_root / ".gitkeep"]
