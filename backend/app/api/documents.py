from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.security import UploadValidationError
from app.services.case_service import get_case, save_document
from app.storage.filesystem import storage
from app.storage.sqlite import db

router = APIRouter(prefix="/api/cases/{case_id}", tags=["documents"])


@router.post("/documents", status_code=201)
async def upload_document(case_id: str, file: UploadFile = File(...), role: str = Form(default="supporting_record")):
    data = await file.read()
    try:
        return save_document(case_id, file.filename, data, role)
    except LookupError as exc:
        raise HTTPException(404, detail={"code": "CASE_NOT_FOUND", "message": str(exc)}) from exc
    except (UploadValidationError, ValueError) as exc:
        raise HTTPException(422, detail={"code": "INVALID_DOCUMENT", "message": str(exc)}) from exc


@router.get("/documents")
def documents(case_id: str):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    return db.all("SELECT id,case_id,filename,category,page_count,sha256,status,role,source_url,created_at FROM documents WHERE case_id=?", (case_id,))


@router.get("/documents/{document_id}/file")
def document_file(case_id: str, document_id: str):
    document = db.one("SELECT * FROM documents WHERE id=? AND case_id=?", (document_id, case_id))
    if not document:
        raise HTTPException(404, "Document not found")
    stored_name = document.get("stored_name", "")
    ext = Path(stored_name).suffix.lower() if stored_name else ".pdf"
    path = storage.document_path(case_id, document_id, extension=ext)
    if not path.exists():
        path = storage.document_path(case_id, document_id)  # fallback to .pdf
    if not path.exists():
        raise HTTPException(404, "Stored document is unavailable")
    mime_types = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".doc": "application/msword"}
    media_type = mime_types.get(ext, "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=document["filename"], content_disposition_type="inline")


@router.get("/documents/{document_id}/pages/{page}")
def document_page(case_id: str, document_id: str, page: int):
    row = db.one("SELECT * FROM pages WHERE case_id=? AND document_id=? AND page_number=?", (case_id, document_id, page))
    if not row:
        raise HTTPException(404, "Page not found")
    import json
    row["blocks"] = json.loads(row.pop("blocks_json"))
    row["document_url"] = f"/api/cases/{case_id}/documents/{document_id}/file#page={page}"
    row["image_url"] = f"/api/cases/{case_id}/documents/{document_id}/pages/{page}/image" if row.get("image_path") else None
    return row


@router.get("/documents/{document_id}/pages/{page}/image")
def document_page_image(case_id: str, document_id: str, page: int):
    row = db.one("SELECT image_path FROM pages WHERE case_id=? AND document_id=? AND page_number=?", (case_id, document_id, page))
    if not row or not row.get("image_path") or not Path(row["image_path"]).exists():
        raise HTTPException(404, "Rendered page image not found")
    return FileResponse(row["image_path"], media_type="image/png")

