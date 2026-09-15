from __future__ import annotations

from pathlib import Path
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.security import ensure_case_path


class DocumentStorageInterface(ABC):
    @abstractmethod
    def document_path(self, case_id: str, document_id: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def write_bytes(self, path: Path, data: bytes) -> None:
        raise NotImplementedError


class DocumentStorage(DocumentStorageInterface):
    def case_dir(self, case_id: str) -> Path:
        path = ensure_case_path(settings.cases_dir, case_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def document_path(self, case_id: str, document_id: str, extension: str = ".pdf") -> Path:
        directory = ensure_case_path(settings.cases_dir, case_id, "documents")
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{document_id}{extension}"

    def page_image_path(self, case_id: str, document_id: str, page: int) -> Path:
        directory = ensure_case_path(settings.cases_dir, case_id, "pages", document_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"page-{page:04d}.png"

    def write_bytes(self, path: Path, data: bytes) -> None:
        path.write_bytes(data)


storage = DocumentStorage()
