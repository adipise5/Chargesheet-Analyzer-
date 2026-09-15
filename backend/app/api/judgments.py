from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.judgment_service import analyze_precedents, list_judgments, save_judgment
from app.services.case_service import get_case
from app.core.runtime_mode import require_writable

router = APIRouter(prefix="/api", tags=["judgments"])


@router.post("/judgments", status_code=201)
async def upload_judgment(file: UploadFile = File(...), title: str = Form(default=""), court: str = Form(default=""), year: str = Form(default="")):
    require_writable()
    try:
        return save_judgment(file.filename, await file.read(), title, court, year)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail={"code": "INVALID_JUDGMENT", "message": str(exc)}) from exc


@router.get("/judgments")
def judgments():
    return list_judgments()


@router.get("/cases/{case_id}/precedents")
def precedents(case_id: str):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    return analyze_precedents(case_id)
