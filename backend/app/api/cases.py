from fastapi import APIRouter, HTTPException

from app.schemas.case import CaseCreate, CaseRecord
from app.services.case_service import create_case, get_case, list_cases
from app.services.demo_service import load_demo_case

router = APIRouter(prefix="/api", tags=["cases"])


@router.post("/cases", response_model=CaseRecord, status_code=201)
def post_case(payload: CaseCreate):
    return create_case(payload.model_dump())


@router.get("/cases", response_model=list[CaseRecord])
def get_cases():
    return list_cases()


@router.get("/cases/{case_id}", response_model=CaseRecord)
def get_case_route(case_id: str):
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, detail={"code": "CASE_NOT_FOUND", "message": "Case not found"})
    return case


@router.post("/demo", response_model=CaseRecord)
def load_demo():
    return load_demo_case()

