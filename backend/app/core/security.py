from __future__ import annotations

import re
from pathlib import Path

PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK"  # ZIP-based format
DOC_MAGIC = b"\xd0\xcf\x11\xe0"  # OLE compound document

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


class UploadValidationError(ValueError):
    pass


def safe_display_filename(filename: str | None) -> str:
    value = Path(filename or "document.pdf").name
    value = re.sub(r"[^\w.()'\- ]+", "_", value, flags=re.UNICODE).strip(" .")
    return (value[:120] or "document.pdf")


def validate_pdf_bytes(data: bytes, filename: str | None, max_bytes: int) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise UploadValidationError("Only PDF files are accepted")
    if not data:
        raise UploadValidationError("The uploaded file is empty")
    if len(data) > max_bytes:
        raise UploadValidationError(f"PDF exceeds the {max_bytes // 1024 // 1024} MB limit")
    if not data.startswith(PDF_MAGIC):
        raise UploadValidationError("File signature is not a valid PDF")


def validate_upload_bytes(data: bytes, filename: str | None, max_bytes: int) -> str:
    """Validate an uploaded file. Returns the detected file type: 'pdf', 'docx', or 'doc'."""
    if not filename:
        raise UploadValidationError("Filename is required")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(f"Accepted formats: PDF, DOC, DOCX. Got: {ext}")
    if not data:
        raise UploadValidationError("The uploaded file is empty")
    if len(data) > max_bytes:
        raise UploadValidationError(f"File exceeds the {max_bytes // 1024 // 1024} MB limit")
    if ext == ".pdf" and not data.startswith(PDF_MAGIC):
        raise UploadValidationError("File signature is not a valid PDF")
    if ext == ".docx" and not data.startswith(DOCX_MAGIC):
        raise UploadValidationError("File signature is not a valid DOCX")
    if ext == ".doc" and not data.startswith(DOC_MAGIC):
        raise UploadValidationError("File signature is not a valid DOC")
    return ext.lstrip(".")


def ensure_case_path(base: Path, case_id: str, *parts: str) -> Path:
    target = (base / case_id / Path(*parts)).resolve()
    case_root = (base / case_id).resolve()
    if case_root != target and case_root not in target.parents:
        raise ValueError("Unsafe storage path")
    return target


