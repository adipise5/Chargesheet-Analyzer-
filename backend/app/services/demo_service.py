from __future__ import annotations

import hashlib
import json
import uuid

from app.graph.repository import graph_repository
from app.services.case_service import create_case, get_case
from app.storage.filesystem import storage
from app.storage.sqlite import db, now_iso


DEMO_CASE_ID = "case_synthetic_demo"
DEMO_DOCUMENT_ID = "doc_synthetic_record"

PAGES = [
    """SYNTHETIC DEMO DATA — NOT A REAL POLICE RECORD
FIR reference: SYN-0001/2026. Station: Training Police Station.
Fictional accused code A1 (Person Alpha / વ્યક્તિ આલ્ફા) is alleged to have used vehicle GJ-99-ZZ-1001.
This record is designed only to test the Chargesheet Intelligence System.""",
    """SYNTHETIC WITNESS STATEMENT W1
Witness code W1 stated that Person Alpha was observed near Training Square at 20:30 on 14/02/2026.
W1 stated the vehicle registration was GJ-99-ZZ-1001. The witness statement is a fictional test artifact.""",
    """SYNTHETIC WITNESS STATEMENT W2
Witness code W2 stated that a similar vehicle reached Training Square at 21:15 on 14/02/2026.
The witness could not identify the driver. Human review is required before associating this claim with A1.""",
    """SYNTHETIC DIGITAL EVIDENCE SUMMARY
CCTV camera CAM-DEMO-7 recorded vehicle GJ-99-ZZ-1001 at Training Square at 20:47 on 14/02/2026.
CDR for fictional mobile number 9000000001 records a tower event in the training zone at 20:45.
Hash: DEMO-SHA256-NOT-REAL. This is synthetic supporting digital material.""",
    """SYNTHETIC SEIZURE MEMO
A training prop vehicle is recorded as GJ-99-ZZ-1010 on 15/02/2026 at 09:10.
Another line in the same demo annexure refers to GJ-99-ZZ-1001.
The near-match is intentional and tests potential registration mismatch detection.""",
    """SYNTHETIC CLAIM WITH LIMITED CORROBORATION
Witness code W7 stated that fictional accused code A2 carried a blue training bag at 19:50 on 14/02/2026.
No linked CCTV, CDR, FSL, or recovery material for this particular blue-bag claim was located in this uploaded synthetic record.""",
    """SYNTHETIC FORENSIC REPORT
FSL-DEMO-22 states that a red synthetic fibre recovered from the training prop vehicle matched a control fibre from Exhibit DEMO-BAG-1.
This result is fictional. Chain-of-custody review remains required.""",
    """SYNTHETIC ANNEXURE INDEX
The index references Annexure DEMO-9, described as an additional camera export. No corresponding Annexure DEMO-9 file is included in this synthetic uploaded record.
ગુજરાતી નોંધ: આ માત્ર કૃત્રિમ પરીક્ષણ માહિતી છે. આ કોઈ વાસ્તવિક કેસ નથી.""",
]


def _write_demo_pdf(path) -> None:
    import fitz
    document = fitz.open()
    for number, content in enumerate(PAGES, start=1):
        page = document.new_page(width=595, height=842)
        page.insert_text((46, 52), f"SYNTHETIC DEMO — PAGE {number}", fontsize=12, fontname="helv", color=(0.05, 0.16, 0.27))
        english_lines = [line for line in content.splitlines() if not any("\u0A80" <= c <= "\u0AFF" for c in line)]
        page.insert_textbox(fitz.Rect(46, 84, 549, 780), "\n\n".join(english_lines), fontsize=11,
                            fontname="helv", lineheight=1.35)
    document.set_metadata({"title": "Synthetic Chargesheet Intelligence Demo", "author": "Generated locally"})
    document.save(path)
    document.close()


def load_demo_case() -> dict:
    existing = get_case(DEMO_CASE_ID)
    if existing:
        return existing
    case = create_case({"case_number": "SYN-DEMO-0001/2026", "police_station": "Training Police Station",
                        "language": "Gujarati / English"}, is_demo=True, case_id=DEMO_CASE_ID)
    pdf_path = storage.document_path(DEMO_CASE_ID, DEMO_DOCUMENT_ID)
    _write_demo_pdf(pdf_path)
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    db.execute("INSERT INTO documents(id,case_id,filename,stored_name,category,page_count,sha256,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
               (DEMO_DOCUMENT_ID, DEMO_CASE_ID, "synthetic-demo-record.pdf", pdf_path.name, "chargesheet", len(PAGES), digest, "processed", now_iso()))
    chunks = []
    for page_number, text in enumerate(PAGES, start=1):
        page_id = f"page_demo_{page_number}"
        chunk_id = f"chunk_demo_{page_number}"
        language = "mixed" if page_number in {1, 8} else "english"
        db.execute("INSERT INTO pages(id,case_id,document_id,page_number,extraction_method,language,original_text,normalized_text,ocr_confidence,review_status,tesseract_text,vision_candidate_text,corrected_text,image_path,blocks_json,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (page_id, DEMO_CASE_ID, DEMO_DOCUMENT_ID, page_number, "native_pdf", language, text, text, 100.0,
                    "accepted", None, None, None, None,
                    json.dumps([{"block_id": f"demo-{page_number}-1", "bounding_box": [46,84,549,780], "original_text": text,
                                 "normalized_text": text, "ocr_engine": "native_pdf", "ocr_confidence": 100,
                                 "review_status": "accepted"}], ensure_ascii=False), now_iso()))
        db.execute("INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
                   (chunk_id, DEMO_CASE_ID, DEMO_DOCUMENT_ID, page_number, text, text.casefold(), language,
                    json.dumps({"ocr_confidence": 100, "synthetic": True})))
        chunks.append({"id": chunk_id, "document_id": DEMO_DOCUMENT_ID, "page_number": page_number,
                       "text": text, "normalized_text": text.casefold(), "language": language,
                       "document_label": "Synthetic demo record"})
    objects, relations = _demo_graph(chunks)
    graph_repository.replace_case(DEMO_CASE_ID, objects, relations)
    findings = _demo_findings()
    with db.connect() as con:
        for finding in findings:
            con.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
                        (finding["id"], DEMO_CASE_ID, finding["type"], json.dumps(finding, ensure_ascii=False)))
    counts = {"total_pages": 8, "native_pages": 8, "ocr_pages": 0, "gujarati_pages": 0, "english_pages": 6,
              "mixed_pages": 2, "low_confidence_pages": 0, "entities": 10, "evidence": 5, "claims": 4,
              "findings": len(findings), "embedding_status": "not generated in deterministic demo"}
    stages = [{"name": name, "state": "complete"} for name in ["PDF validated", "Pages identified", "Native text extracted",
              "Scanned pages identified", "OCR processing", "Entity extraction", "Entity resolution", "Building case graph",
              "Creating embeddings", "Analysing claims", "Checking contradictions", "Verifying findings"]]
    db.execute("INSERT INTO jobs(id,case_id,state,stage,progress,counts_json,stages_json,error,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
               ("job_demo", DEMO_CASE_ID, "complete", "Verifying findings", 100, json.dumps(counts), json.dumps(stages), None, now_iso()))
    db.audit("demo_loaded", DEMO_CASE_ID, {"count": 8})
    return case


def _citation(page: int, label: str) -> dict:
    return {"document_id": DEMO_DOCUMENT_ID, "page": page, "chunk_id": f"chunk_demo_{page}", "label": label}


def _demo_graph(chunks: list[dict]) -> tuple[list[dict], list[dict]]:
    objects = [
        {"id": DEMO_CASE_ID, "kind": "Case", "subtype": "case", "label": "SYN-DEMO-0001/2026", "confidence": 1, "data": {"synthetic": True}},
        {"id": DEMO_DOCUMENT_ID, "kind": "Document", "subtype": "chargesheet", "label": "Synthetic demo record", "confidence": 1, "data": {"page_count": 8}},
        {"id": "accused_a1", "kind": "Accused", "subtype": "accused", "label": "Person Alpha / વ્યક્તિ આલ્ફા", "confidence": .98, "data": {"aliases": ["A1", "Person Alpha"]}},
        {"id": "accused_a2", "kind": "Accused", "subtype": "accused", "label": "Person Beta / વ્યક્તિ બીટા", "confidence": .82, "data": {"aliases": ["A2", "Person Beta"]}},
        {"id": "witness_w1", "kind": "Witness", "subtype": "witness", "label": "Witness W1", "confidence": 1, "data": {}},
        {"id": "witness_w2", "kind": "Witness", "subtype": "witness", "label": "Witness W2", "confidence": 1, "data": {}},
        {"id": "witness_w7", "kind": "Witness", "subtype": "witness", "label": "Witness W7", "confidence": 1, "data": {}},
        {"id": "location_training_square", "kind": "Location", "subtype": "location", "label": "Training Square", "confidence": 1, "data": {}},
        {"id": "vehicle_demo", "kind": "Vehicle", "subtype": "vehicle", "label": "GJ-99-ZZ-1001", "confidence": .96, "data": {"variants": ["GJ-99-ZZ-1010"]}},
        {"id": "claim_presence", "kind": "Claim", "subtype": "presence", "label": "A1 present near Training Square", "confidence": .86, "data": {}},
        {"id": "claim_time_w2", "kind": "Claim", "subtype": "time", "label": "Similar vehicle reached at 21:15", "confidence": .74, "data": {}},
        {"id": "claim_blue_bag", "kind": "Claim", "subtype": "possession", "label": "A2 carried a blue training bag", "confidence": .63, "data": {}},
        {"id": "evidence_cctv", "kind": "DigitalEvidence", "subtype": "cctv", "label": "CAM-DEMO-7 CCTV", "confidence": .94, "data": {}},
        {"id": "evidence_cdr", "kind": "DigitalEvidence", "subtype": "cdr", "label": "Synthetic CDR tower event", "confidence": .88, "data": {}},
        {"id": "evidence_fsl", "kind": "ForensicEvidence", "subtype": "fsl", "label": "FSL-DEMO-22 fibre result", "confidence": .87, "data": {}},
        {"id": "event_observed", "kind": "Event", "subtype": "incident", "label": "Vehicle observed at Training Square", "confidence": .84, "data": {"date": "14/02/2026", "time": "20:47"}},
    ]
    objects += [{"id": chunk["id"], "kind": "TextChunk", "subtype": "source", "label": f"Synthetic source page {chunk['page_number']}",
                 "confidence": 1, "data": {"document_id": DEMO_DOCUMENT_ID, "page_number": chunk["page_number"]}} for chunk in chunks]
    relations = [{"id": "rel_doc_case", "case_id": DEMO_CASE_ID, "source_id": DEMO_DOCUMENT_ID, "target_id": DEMO_CASE_ID,
                  "relation": "PART_OF", "confidence": 1, "citations": [], "extraction_method": "system", "human_verified": True}]
    specs = [
        ("witness_w1", "claim_presence", "MAKES_CLAIM", 2), ("claim_presence", "accused_a1", "SUBJECT_OF", 2),
        ("claim_presence", "event_observed", "ABOUT_EVENT", 2), ("event_observed", "location_training_square", "OCCURRED_AT", 2),
        ("evidence_cctv", "claim_presence", "SUPPORTS", 4), ("evidence_cdr", "claim_presence", "SUPPORTS", 4),
        ("vehicle_demo", "evidence_cctv", "CAPTURED_BY", 4), ("witness_w2", "claim_time_w2", "MAKES_CLAIM", 3),
        ("claim_time_w2", "claim_presence", "CONTRADICTS", 3), ("witness_w7", "claim_blue_bag", "MAKES_CLAIM", 6),
        ("claim_blue_bag", "accused_a2", "SUBJECT_OF", 6), ("evidence_fsl", "vehicle_demo", "RELATES_TO", 7),
    ]
    for i, (source, target, relation, page) in enumerate(specs):
        relations.append({"id": f"rel_demo_{i}", "case_id": DEMO_CASE_ID, "source_id": source, "target_id": target,
                          "relation": relation, "confidence": .9 if relation != "CONTRADICTS" else .78,
                          "citations": [_citation(page, f"Synthetic source — p{page}")],
                          "extraction_method": "synthetic_seed", "human_verified": True})
    for page in range(1, 9):
        relations.append({"id": f"rel_chunk_{page}", "case_id": DEMO_CASE_ID, "source_id": f"chunk_demo_{page}",
                          "target_id": DEMO_DOCUMENT_ID, "relation": "PART_OF", "confidence": 1, "citations": [],
                          "extraction_method": "system", "human_verified": True})
    return objects, relations


def _finding(fid: str, kind: str, title: str, summary: str, classification: str, confidence: float,
             supporting: list[dict], contradicting: list[dict] | None = None, entities: list[str] | None = None,
             review: bool = False, factors: dict | None = None) -> dict:
    return {"id": fid, "type": kind, "title": title, "summary": summary, "classification": classification,
            "confidence": confidence, "supporting_sources": supporting, "contradicting_sources": contradicting or [],
            "entities": entities or [], "factors": factors or {}, "human_review_required": review, "verified": True}


def _demo_findings() -> list[dict]:
    return [
        _finding("finding_demo_strong", "strong_point", "Vehicle at Training Square", "Witness W1, synthetic CCTV, and a fictional CDR tower event independently reference the vehicle or training zone around the reported period.",
                 "STRONGLY_CORROBORATED", .91, [_citation(2, "Witness W1"), _citation(4, "CCTV and CDR")], entities=["A1", "GJ-99-ZZ-1001", "Training Square"],
                 factors={"number_of_supporting_sources": 3, "number_of_independent_source_types": 3, "witness_support": 1, "digital_support": 2, "contradicting_sources": 1}),
        _finding("finding_demo_weak", "weak_point", "Blue training bag allegation involving A2", "Only Witness W7 supports this synthetic allegation. No linked CCTV, CDR, FSL, or recovery material was located in the uploaded record.",
                 "LIMITED_CORROBORATION", .67, [_citation(6, "Witness W7")], entities=["A2"], review=True,
                 factors={"number_of_supporting_sources": 1, "number_of_independent_source_types": 1}),
        _finding("finding_demo_contradiction", "contradiction", "Vehicle time inconsistency", "Witness W1 states 20:30, the CCTV summary states 20:47, and Witness W2 states 21:15. The 45-minute span requires event-identity review.",
                 "CONFLICTING_EVIDENCE", .88, [], [_citation(2, "Witness W1 — 20:30"), _citation(3, "Witness W2 — 21:15"), _citation(4, "CCTV — 20:47")], review=True,
                 factors={"contradicting_sources": 3, "timeline_consistency": .42}),
        _finding("finding_demo_mistake", "potential_mistake", "Vehicle registration mismatch", "The record contains GJ-99-ZZ-1001 and GJ-99-ZZ-1010. This is a potential transcription or recording inconsistency.",
                 "REVIEW_REQUIRED", .93, [_citation(1, "GJ-99-ZZ-1001"), _citation(5, "GJ-99-ZZ-1010 and GJ-99-ZZ-1001")], entities=["GJ-99-ZZ-1001", "GJ-99-ZZ-1010"], review=True,
                 factors={"variant_count": 2}),
        _finding("finding_demo_missing", "missing_link", "Referenced Annexure DEMO-9 not linked", "The index references an additional camera export, but no linked Annexure DEMO-9 was located in the uploaded record.",
                 "INSUFFICIENT_INFORMATION", .9, [_citation(8, "Synthetic annexure index")], review=True,
                 factors={"referenced_documents": 1, "linked_documents": 0}),
    ]
