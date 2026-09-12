from app.analysis.comparative import comparative_findings, completeness_findings


def chunk(document_id: str, text: str, page: int = 1) -> dict:
    return {"id": f"chunk_{document_id}", "document_id": document_id, "page_number": page,
            "text": text, "language": "english"}


def test_cross_document_vehicle_difference_contains_structured_explanation():
    documents = [{"id": "draft", "filename": "draft.pdf", "role": "draft_chargesheet"},
                 {"id": "fir", "filename": "fir.pdf", "role": "fir"}]
    findings = comparative_findings(documents, [chunk("draft", "Vehicle GJ-01-AA-1234"),
                                                chunk("fir", "Vehicle GJ-01-AA-5678")])
    assert any(item["type"] == "potential_mistake" and item["differences"] and item["io_action"] for item in findings)


def test_draft_without_expected_records_is_flagged():
    documents = [{"id": "draft", "filename": "draft.pdf", "role": "draft_chargesheet"}]
    findings = completeness_findings(documents, [chunk("draft", "Accused A1 is charged under section 302")])
    assert {item["related_document_roles"][1] for item in findings} >= {"fir", "medical_report", "forensic_report"}
