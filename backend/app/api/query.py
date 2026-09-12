from fastapi import APIRouter, HTTPException

from app.schemas.query import QueryRequest, QueryResponse
from app.services.case_service import get_case
from app.services.query_service import query_case

router = APIRouter(prefix="/api/cases/{case_id}", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(case_id: str, payload: QueryRequest):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    return query_case(case_id, payload.question)

