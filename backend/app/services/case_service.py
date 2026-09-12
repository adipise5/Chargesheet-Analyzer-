from __future__ import annotations

import hashlib
import json
import uuid

from app.core.config import settings
from app.core.security import safe_display_filename, validate_pdf_bytes
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


def list_cases() -> list[dict]:
    rows = db.all("SELECT * FROM cases ORDER BY updated_at DESC")
    for row in rows:
        row["is_demo"] = bool(row["is_demo"])
    return rows


def save_document(case_id: str, filename: str | None, data: bytes, role: str = "supporting_record") -> dict:
    if not get_case(case_id):
        raise LookupError("Case not found")
    validate_pdf_bytes(data, filename, settings.max_upload_bytes)
    digest = hashlib.sha256(data).hexdigest()
    duplicate = db.one("SELECT * FROM documents WHERE case_id=? AND sha256=?", (case_id, digest))
    if duplicate:
        return duplicate
    document_id = f"doc_{uuid.uuid4().hex}"
    path = storage.document_path(case_id, document_id)
    storage.write_bytes(path, data)
    try:
        inspection = inspect_pdf(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    display_name = safe_display_filename(filename)
    allowed_roles = {"draft_chargesheet", "fir", "case_diary", "witness_statement", "medical_report",
                     "forensic_report", "cctv_record", "seizure_memo", "supporting_record"}
    role = role if role in allowed_roles else "supporting_record"
    db.execute(
        "INSERT INTO documents(id,case_id,filename,stored_name,category,page_count,sha256,status,role,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (document_id, case_id, display_name, path.name, "unknown", inspection["page_count"], digest, "uploaded", role, now_iso()),
    )
    db.execute("UPDATE cases SET status='uploaded',updated_at=? WHERE id=?", (now_iso(), case_id))
    db.audit("file_uploaded", case_id, {"document_id": document_id, "count": inspection["page_count"]})
    return db.one("SELECT * FROM documents WHERE id=?", (document_id,))


def status_payload(case_id: str) -> dict:
    job = db.one("SELECT * FROM jobs WHERE case_id=?", (case_id,))
    if not job:
        return {"state": get_case(case_id)["status"] if get_case(case_id) else "not_found", "stage": "waiting",
                "progress": 0, "counts": {}, "stages": [], "error": None}
    return {**job, "counts": json.loads(job.pop("counts_json")), "stages": json.loads(job.pop("stages_json"))}

