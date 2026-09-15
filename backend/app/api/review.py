from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.runtime_mode import require_writable
from app.services.case_service import get_case
from app.storage.sqlite import db, now_iso

router = APIRouter(prefix="/api/cases/{case_id}/ocr", tags=["review"])


class ReviewUpdate(BaseModel):
    status: Literal["accepted", "needs_review", "human_corrected"]
    corrected_text: str | None = Field(default=None, max_length=200000)


@router.get("/review")
def review_queue(case_id: str):
    if not get_case(case_id):
        raise HTTPException(404, "Case not found")
    rows = db.all("SELECT p.*,d.filename FROM pages p JOIN documents d ON d.id=p.document_id WHERE p.case_id=? AND p.review_status='needs_review' ORDER BY p.document_id,p.page_number", (case_id,))
    for row in rows:
        row["blocks"] = json.loads(row.pop("blocks_json"))
        row["document_url"] = f"/api/cases/{case_id}/documents/{row['document_id']}/file#page={row['page_number']}"
    return rows


@router.patch("/review/{page_id}")
def update_review(case_id: str, page_id: str, payload: ReviewUpdate):
    require_writable()
    from app.extraction.entity_resolution import normalize_text
    row = db.one("SELECT * FROM pages WHERE id=? AND case_id=?", (page_id, case_id))
    if not row:
        raise HTTPException(404, "Page not found")
    corrected = payload.corrected_text if payload.status == "human_corrected" else row.get("corrected_text")
    if payload.status == "human_corrected" and not corrected:
        raise HTTPException(422, "Corrected text is required")
    effective = corrected or row["original_text"]
    db.execute("UPDATE pages SET review_status=?,corrected_text=?,normalized_text=?,updated_at=? WHERE id=?",
               (payload.status, corrected, normalize_text(effective), now_iso(), page_id))
    _rebuild_from_review(case_id, row["document_id"], row["page_number"], effective)
    db.audit("ocr_manually_corrected" if corrected else "ocr_reviewed", case_id,
             {"document_id": row["document_id"], "page": row["page_number"]})
    return {"id": page_id, "review_status": payload.status, "updated_at": now_iso()}


def _rebuild_from_review(case_id: str, document_id: str, page_number: int, text: str) -> None:
    from app.extraction.entity_resolution import normalize_text
    from app.graph.builder import build_graph
    from app.graph.repository import graph_repository
    from app.services.analysis_service import generate_findings
    from app.services.processing_service import chunk_text
    with db.connect() as con:
        con.execute("DELETE FROM chunks WHERE case_id=? AND document_id=? AND page_number=?", (case_id, document_id, page_number))
        for index, body in enumerate(chunk_text(text), start=1):
            con.execute("INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
                        (f"chunk_{document_id}_{page_number}_{index}", case_id, document_id, page_number, body,
                         normalize_text(body), "mixed", json.dumps({"human_corrected": True})))
    case = get_case(case_id)
    documents = db.all("SELECT * FROM documents WHERE case_id=?", (case_id,))
    chunks = db.all("SELECT c.*,d.filename document_label FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.case_id=?", (case_id,))
    objects, relations = build_graph(case, documents, chunks)
    graph_repository.replace_case(case_id, objects, relations)
    generate_findings(case_id, objects, chunks)

