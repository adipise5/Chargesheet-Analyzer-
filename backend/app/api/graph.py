from fastapi import APIRouter, HTTPException

from app.graph.repository import graph_repository
from app.services.case_service import get_case

router = APIRouter(prefix="/api/cases/{case_id}", tags=["graph"])


@router.get("/graph")
def graph(case_id: str):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    return graph_repository.data(case_id)

