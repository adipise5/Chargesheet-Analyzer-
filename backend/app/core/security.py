from __future__ import annotations

import re
from pathlib import Path

PDF_MAGIC = b"%PDF-"


class UploadValidationError(ValueError):
    pass


def safe_display_filename(filename: str | None) -> str:
    value = Path(filename or "document.pdf").name
    value = re.sub(r"[^\w.()\- ]+", "_", value, flags=re.UNICODE).strip(" .")
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


def ensure_case_path(base: Path, case_id: str, *parts: str) -> Path:
    target = (base / case_id / Path(*parts)).resolve()
    case_root = (base / case_id).resolve()
    if case_root != target and case_root not in target.parents:
        raise ValueError("Unsafe storage path")
    return target

