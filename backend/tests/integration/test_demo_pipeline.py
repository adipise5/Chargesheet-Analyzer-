from app.services.demo_service import load_demo_case
from app.services.analysis_service import get_findings
from app.services.query_service import query_case
from app.graph.repository import graph_repository
from app.services.case_service import create_case, save_document
from app.services.processing_service import process_case
from app.storage.sqlite import db


def test_synthetic_demo_populates_full_case():
    case = load_demo_case()
    graph = graph_repository.data(case["id"])
    findings = get_findings(case["id"])
    assert len(graph["nodes"]) >= 20
    assert any(edge["relation"] == "CONTRADICTS" and edge["citations"] for edge in graph["edges"])
    assert {item["type"] for item in findings} == {"strong_point", "weak_point", "contradiction", "potential_mistake", "missing_link"}
    assert all(item["verified"] and (item["supporting_sources"] or item["contradicting_sources"]) for item in findings)


def test_demo_graphrag_returns_citations():
    case = load_demo_case()
    response = query_case(case["id"], "What evidence connects A1 with the vehicle?")
    assert response["citations"]
    assert all(citation["page"] > 0 for citation in response["citations"])


def test_native_pdf_runs_real_processing_pipeline(tmp_path):
    import fitz
    source = tmp_path / "synthetic.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(fitz.Rect(40, 40, 550, 780),
                        "SYNTHETIC TEST DATA. Witness W9 stated that fictional vehicle GJ-99-ZZ-1001 was observed at 20:30 on 14/02/2026. CCTV and a digital report recorded the same fictional vehicle.",
                        fontsize=11)
    pdf.save(source)
    pdf.close()
    case = create_case({"case_number": "SYN-PIPELINE", "police_station": "Training", "language": "English"})
    save_document(case["id"], "synthetic.pdf", source.read_bytes())
    process_case(case["id"])
    stored = db.one("SELECT status FROM cases WHERE id=?", (case["id"],))
    page_row = db.one("SELECT extraction_method,ocr_confidence FROM pages WHERE case_id=?", (case["id"],))
    assert stored["status"] == "ready"
    assert page_row == {"extraction_method": "native_pdf", "ocr_confidence": 100.0}
    assert graph_repository.data(case["id"])["nodes"]
