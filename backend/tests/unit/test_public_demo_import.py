import copy
from pathlib import Path

import pytest

from scripts import import_public_demo as importer
from app.services.case_service import create_case, save_document
from app.storage.sqlite import Database, db


def test_public_catalog_has_six_usable_records_and_four_explicit_unavailable_sources():
    usable, unavailable = importer._assert_catalog(importer._load_catalog())
    assert len(usable) == 6
    assert len([item for item in usable if item["source_type"] == "public_judgment"]) == 5
    assert len(unavailable) == 4
    assert all(item["status"] == "unavailable_404" for item in unavailable)
    assert all(item["page_count"] > 0 and len(item["sha256"]) == 64 for item in usable)


def test_public_case_ids_are_deterministic_and_safe():
    assert importer._slug("judgment_sharif_ahmad") == "judgment-sharif-ahmad"
    assert importer._slug("Judgment / Sajid") == "judgment-sajid"
    assert importer._slug("judgment_sharif_ahmad") == importer._slug("judgment_sharif_ahmad")


def test_public_catalog_rejects_duplicate_artifacts():
    sources = importer._load_catalog()
    duplicate = copy.deepcopy(sources[0])
    duplicate["id"] = "duplicate-educational-artifact"
    sources.append(duplicate)
    with pytest.raises(importer.SourceRejected, match="reuses a verified artifact"):
        importer._assert_catalog(sources)


def test_public_catalog_rejects_non_pdf_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    html = tmp_path / "not-a-pdf.html"
    html.write_text("<html>not a public document</html>", encoding="utf-8")
    monkeypatch.setattr(importer, "_safe_artifact_path", lambda _: html)
    source = {
        "id": "invalid-html",
        "title": "Invalid source",
        "source_type": "public_judgment",
        "status": "verified_pdf",
        "url": "https://example.invalid/source",
        "artifact": "demo_snapshot/not-a-pdf.html",
    }
    with pytest.raises(importer.SourceRejected, match="not a PDF"):
        importer._assert_catalog([source])


def test_record_metadata_is_persisted_and_exposed_on_documents():
    import fitz

    case = create_case({"case_number": "PUBLIC-METADATA", "police_station": "Reference Court",
                        "record_type": "public_judgment"})
    assert case["record_type"] == "public_judgment"
    document = fitz.open()
    document.new_page().insert_text((40, 40), "Public source test")
    payload = document.tobytes()
    document.close()
    saved = save_document(case["id"], "public.pdf", payload, source_url="https://example.invalid/public")
    assert saved["source_url"] == "https://example.invalid/public"
    assert db.one("SELECT source_url FROM documents WHERE id=?", (saved["id"],))["source_url"] == "https://example.invalid/public"


def test_old_database_migration_adds_public_metadata_columns(tmp_path: Path):
    legacy = tmp_path / "legacy.db"
    import sqlite3

    with sqlite3.connect(legacy) as connection:
        connection.executescript("""
            CREATE TABLE cases (
              id TEXT PRIMARY KEY, case_number TEXT NOT NULL, police_station TEXT NOT NULL,
              language TEXT NOT NULL, status TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE documents (
              id TEXT PRIMARY KEY, case_id TEXT NOT NULL, filename TEXT NOT NULL,
              stored_name TEXT NOT NULL, category TEXT NOT NULL, page_count INTEGER NOT NULL,
              sha256 TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
            );
        """)
    migrated = Database(legacy)
    migrated.initialize()
    assert "record_type" in {row["name"] for row in migrated.all("PRAGMA table_info(cases)")}
    assert "source_url" in {row["name"] for row in migrated.all("PRAGMA table_info(documents)")}
