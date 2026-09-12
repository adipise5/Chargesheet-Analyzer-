from __future__ import annotations

import json
import uuid

from app.agents.timeline_agent import timeline_from_objects
from app.core.config import settings
from app.extraction.document_classifier import classify_document
from app.extraction.entity_resolution import normalize_text
from app.graph.builder import build_graph
from app.graph.repository import graph_repository
from app.ingestion.page_renderer import render_page
from app.ocr.router import DigitalPDFProvider, OCRRouter
from app.ocr.tesseract_provider import TesseractOCRProvider
from app.ocr.vision_verifier import VisionOCRVerifier
from app.services.analysis_service import generate_findings
from app.services.embedding_service import OllamaEmbeddingProvider
from app.storage.filesystem import storage
from app.storage.sqlite import db, now_iso


STAGE_NAMES = [
    "PDF validated", "Pages identified", "Native text extracted", "Scanned pages identified",
    "OCR processing", "Entity extraction", "Entity resolution", "Building case graph",
    "Creating embeddings", "Analysing claims", "Checking contradictions", "Verifying findings",
]


def _stage_rows(current: int) -> list[dict]:
    return [{"name": name, "state": "complete" if i < current else "active" if i == current else "pending"}
            for i, name in enumerate(STAGE_NAMES)]


def _job(case_id: str, state: str, stage_index: int, progress: int, counts: dict, error: str | None = None) -> None:
    db.execute(
        "INSERT INTO jobs(id,case_id,state,stage,progress,counts_json,stages_json,error,updated_at) VALUES(?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(case_id) DO UPDATE SET state=excluded.state,stage=excluded.stage,progress=excluded.progress,counts_json=excluded.counts_json,stages_json=excluded.stages_json,error=excluded.error,updated_at=excluded.updated_at",
        (f"job_{case_id}", case_id, state, STAGE_NAMES[min(stage_index, len(STAGE_NAMES)-1)], progress,
         json.dumps(counts), json.dumps(_stage_rows(stage_index)), error, now_iso()),
    )


def chunk_text(text: str, size: int = 1400, overlap: int = 180) -> list[str]:
    if not text.strip():
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            split = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
            if split > start + size // 2:
                end = split
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def process_case(case_id: str) -> None:
    counts = {"total_pages": 0, "native_pages": 0, "ocr_pages": 0, "gujarati_pages": 0,
              "english_pages": 0, "mixed_pages": 0, "low_confidence_pages": 0,
              "entities": 0, "evidence": 0, "claims": 0}
    try:
        case = db.one("SELECT * FROM cases WHERE id=?", (case_id,))
        documents = db.all("SELECT * FROM documents WHERE case_id=?", (case_id,))
        if not case or not documents:
            raise ValueError("A case with at least one uploaded PDF is required")
        db.execute("UPDATE cases SET status='processing',updated_at=? WHERE id=?", (now_iso(), case_id))
        db.audit("processing_started", case_id)
        _job(case_id, "running", 0, 2, counts)
        with db.connect() as con:
            con.execute("DELETE FROM pages WHERE case_id=?", (case_id,))
            con.execute("DELETE FROM chunks WHERE case_id=?", (case_id,))
        digital = DigitalPDFProvider()
        tesseract = TesseractOCRProvider()
        vision = VisionOCRVerifier()
        router = OCRRouter(digital, tesseract, vision, settings.ocr_confidence_threshold)
        all_chunks: list[dict] = []
        import fitz
        total_pages = sum(document["page_count"] for document in documents)
        counts["total_pages"] = total_pages
        _job(case_id, "running", 1, 7, counts)
        processed = 0
        for document in documents:
            path = storage.document_path(case_id, document["id"])
            pdf = fitz.open(path)
            sample = "".join(pdf[i].get_text("text") for i in range(min(4, pdf.page_count)))
            category, _ = classify_document(sample)
            role_from_category = {"chargesheet": "draft_chargesheet", "fir": "fir", "witness_statement": "witness_statement",
                                  "medical_report": "medical_report", "fsl_report": "forensic_report", "cdr": "supporting_record",
                                  "cctv_record": "cctv_record", "case_diary": "case_diary", "seizure_memo": "seizure_memo"}
            role = document.get("role", "supporting_record")
            if role == "supporting_record" and category in role_from_category:
                role = role_from_category[category]
            db.execute("UPDATE documents SET category=?,role=?,status='processing' WHERE id=?", (category, role, document["id"]))
            document["category"] = category
            document["role"] = role
            for index, page in enumerate(pdf):
                image_path = None
                native = digital.extract_page(page)
                if len(normalize_text(native.text)) >= 40:
                    result, candidate, review = native, None, "accepted"
                    counts["native_pages"] += 1
                else:
                    image_path = storage.page_image_path(case_id, document["id"], index + 1)
                    render_page(page, image_path)
                    result, candidate, review = router.route(page, image_path)
                    counts["ocr_pages"] += 1
                if result.language in {"gujarati", "english", "mixed"}:
                    counts[f"{result.language}_pages"] += 1
                if review == "needs_review":
                    counts["low_confidence_pages"] += 1
                page_id = f"page_{document['id']}_{index+1}"
                block_data = [{"block_id": b.block_id, "bounding_box": list(b.bounding_box),
                               "original_text": b.text, "normalized_text": normalize_text(b.text),
                               "ocr_engine": result.engine, "ocr_confidence": b.confidence,
                               "review_status": review} for b in result.blocks]
                db.execute(
                    "INSERT INTO pages(id,case_id,document_id,page_number,extraction_method,language,original_text,normalized_text,ocr_confidence,review_status,tesseract_text,vision_candidate_text,corrected_text,image_path,blocks_json,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (page_id, case_id, document["id"], index+1, result.engine, result.language, result.text,
                     normalize_text(result.text), result.confidence, review, result.text if result.engine.startswith("tesseract") else None,
                     candidate.text if candidate else None, None, str(image_path) if image_path else None,
                     json.dumps(block_data, ensure_ascii=False), now_iso()),
                )
                for chunk_index, body in enumerate(chunk_text(result.text)):
                    chunk = {"id": f"chunk_{document['id']}_{index+1}_{chunk_index+1}", "case_id": case_id,
                             "document_id": document["id"], "document_label": document["filename"],
                             "page_number": index+1, "text": body, "normalized_text": normalize_text(body),
                             "language": result.language, "confidence": result.confidence / 100}
                    all_chunks.append(chunk)
                    db.execute("INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
                               (chunk["id"], case_id, document["id"], index+1, body, chunk["normalized_text"], result.language,
                                json.dumps({"ocr_confidence": result.confidence})))
                processed += 1
                _job(case_id, "running", 4 if counts["ocr_pages"] else 2, 10 + int(35 * processed / max(total_pages, 1)), counts)
            pdf.close()
            db.execute("UPDATE documents SET status='processed' WHERE id=?", (document["id"],))
        db.audit("ocr_completed", case_id, {"count": counts["ocr_pages"]})
        _job(case_id, "running", 5, 52, counts)
        objects, relations = build_graph(case, documents, all_chunks)
        counts["entities"] = sum(o["kind"] in {"Vehicle", "Device", "LegalSection", "Person", "Accused", "Witness"} for o in objects)
        counts["evidence"] = sum(o["kind"] == "Evidence" for o in objects)
        counts["claims"] = sum(o["kind"] == "Claim" for o in objects)
        _job(case_id, "running", 7, 68, counts)
        graph_repository.replace_case(case_id, objects, relations)
        db.audit("graph_built", case_id, {"count": len(objects)})
        _job(case_id, "running", 8, 76, counts)
        try:
            provider = OllamaEmbeddingProvider()
            for start in range(0, len(all_chunks), 8):
                batch = all_chunks[start:start+8]
                vectors = provider.embed([item["text"] for item in batch])
                for item, vector in zip(batch, vectors):
                    db.execute("UPDATE chunks SET embedding_json=? WHERE id=?", (json.dumps(vector), item["id"]))
        except Exception as exc:
            counts["embedding_status"] = f"local model unavailable: {exc}"
        _job(case_id, "running", 9, 84, counts)
        findings = generate_findings(case_id, objects, all_chunks)
        counts["findings"] = len(findings)
        _job(case_id, "running", 11, 96, counts)
        db.execute("UPDATE cases SET status='ready',updated_at=? WHERE id=?", (now_iso(), case_id))
        db.audit("finding_verified", case_id, {"count": sum(f["verified"] for f in findings)})
        _job(case_id, "complete", len(STAGE_NAMES), 100, counts)
    except Exception as exc:
        db.execute("UPDATE cases SET status='error',updated_at=? WHERE id=?", (now_iso(), case_id))
        _job(case_id, "error", 0, 0, counts, str(exc))

