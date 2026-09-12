from pathlib import Path

import pytest

from app.storage.filesystem import storage
from app.storage.sqlite import db


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db.path = tmp_path / "test.db"
    db.initialize()

    def document_path(case_id: str, document_id: str) -> Path:
        path = tmp_path / "cases" / case_id / "documents" / f"{document_id}.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def page_image_path(case_id: str, document_id: str, page: int) -> Path:
        path = tmp_path / "cases" / case_id / "pages" / document_id / f"page-{page:04d}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(storage, "document_path", document_path)
    monkeypatch.setattr(storage, "page_image_path", page_image_path)
    yield

