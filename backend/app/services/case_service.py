from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.security import safe_display_filename, validate_upload_bytes, UploadValidationError
from app.ingestion.pdf_loader import inspect_pdf
from app.storage.filesystem import storage
from app.storage.sqlite import db, now_iso


def create_case(payload: dict, *, is_demo: bool = False, case_id: str | None = None) -> dict:
    identifier = case_id or f"case_{uuid.uuid4().hex}"
    timestamp = now_iso()
    db.execute(
        "INSERT INTO cases(id,case_number,police_station,language,status,is_demo,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
        (identifier, payload["case_number"], payload.get("police_station", "Not specified"),
         payload.get("language", "Gujarati / English"), "ready" if is_demo else "created", int(is_demo), timestamp, timestamp),
    )
    db.audit("case_created", identifier)
    return get_case(identifier)


def get_case(case_id: str) -> dict | None:
    row = db.one("SELECT * FROM cases WHERE id=?", (case_id,))
    if row:
        row["is_demo"] = bool(row["is_demo"])
    return row


def get_case_by_number(case_number: str) -> dict | None:
    """Look up a case by its case_number field (for linking multiple documents to the same case)."""
    row = db.one("SELECT * FROM cases WHERE case_number=? ORDER BY updated_at DESC LIMIT 1", (case_number,))
    if row:
        row["is_demo"] = bool(row["is_demo"])
    return row


def list_cases() -> list[dict]:
    rows = db.all("SELECT * FROM cases ORDER BY updated_at DESC")
    for row in rows:
        row["is_demo"] = bool(row["is_demo"])
    return rows


def delete_case(case_id: str) -> bool:
    if not get_case(case_id):
        return False
    # Manually delete rows for tables without CASCADE
    db.execute("DELETE FROM chunks WHERE case_id=?", (case_id,))
    db.execute("DELETE FROM objects WHERE case_id=?", (case_id,))
    db.execute("DELETE FROM relations WHERE case_id=?", (case_id,))
    db.execute("DELETE FROM findings WHERE case_id=?", (case_id,))
    db.execute("DELETE FROM jobs WHERE case_id=?", (case_id,))
    db.execute("DELETE FROM audits WHERE case_id=?", (case_id,))
    # Delete the case (will cascade to documents and pages if configured)
    db.execute("DELETE FROM cases WHERE id=?", (case_id,))
    
    import shutil
    case_dir = settings.cases_dir / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir, ignore_errors=True)
    return True


def save_document(case_id: str, filename: str | None, data: bytes, role: str = "supporting_record") -> dict:
    if not get_case(case_id):
        raise LookupError("Case not found")
    file_type = validate_upload_bytes(data, filename, settings.max_upload_bytes)
    digest = hashlib.sha256(data).hexdigest()
    duplicate = db.one("SELECT * FROM documents WHERE case_id=? AND sha256=?", (case_id, digest))
    if duplicate:
        return duplicate
    document_id = f"doc_{uuid.uuid4().hex}"
    # Use the original extension in the stored name so processing can detect file type
    ext = Path(filename or "document.pdf").suffix.lower()
    stored_name = f"{document_id}{ext}"
    path = storage.document_path(case_id, document_id, extension=ext)
    storage.write_bytes(path, data)
    try:
        if file_type == "pdf":
            inspection = inspect_pdf(path)
            page_count = inspection["page_count"]
        else:
            # Word documents: estimate page count from text length
            from app.ingestion.word_loader import extract_word_text
            text = extract_word_text(path)
            # ~3000 chars per page is a reasonable estimate
            page_count = max(1, len(text) // 3000 + (1 if len(text) % 3000 else 0))
    except Exception:
        path.unlink(missing_ok=True)
        raise
    display_name = safe_display_filename(filename)
    allowed_roles = {"draft_chargesheet", "fir", "case_diary", "witness_statement", "medical_report",
                     "forensic_report", "cctv_record", "seizure_memo", "supporting_record"}
    role = role if role in allowed_roles else "supporting_record"
    db.execute(
        "INSERT INTO documents(id,case_id,filename,stored_name,category,page_count,sha256,status,role,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (document_id, case_id, display_name, stored_name, "unknown", page_count, digest, "uploaded", role, now_iso()),
    )
    db.execute("UPDATE cases SET status='uploaded',updated_at=? WHERE id=?", (now_iso(), case_id))
    db.audit("file_uploaded", case_id, {"document_id": document_id, "count": page_count})
    return db.one("SELECT * FROM documents WHERE id=?", (document_id,))


def status_payload(case_id: str) -> dict:
    job = db.one("SELECT * FROM jobs WHERE case_id=?", (case_id,))
    if not job:
        return {"state": get_case(case_id)["status"] if get_case(case_id) else "not_found", "stage": "waiting",
                "progress": 0, "counts": {}, "stages": [], "error": None}
    return {**job, "counts": json.loads(job.pop("counts_json")), "stages": json.loads(job.pop("stages_json"))}
