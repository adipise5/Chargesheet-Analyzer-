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
