from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.case_service import get_case, status_payload
from app.core.runtime_mode import require_writable
from app.services.processing_service import process_case

router = APIRouter(prefix="/api/cases/{case_id}", tags=["processing"])


@router.post("/process", status_code=202)
def start_processing(case_id: str, background_tasks: BackgroundTasks):
    require_writable()
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    status = status_payload(case_id)
    if status["state"] == "running":
        return status
    background_tasks.add_task(process_case, case_id)
    return {"state": "queued", "case_id": case_id}


@router.get("/status")
def processing_status(case_id: str):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    return status_payload(case_id)

