from app.api import analysis
from app.services.case_service import create_case


def test_overview_reuses_summary_until_case_content_changes(monkeypatch):
    case = create_case({"case_number": "SUMMARY-CACHE", "police_station": "Training"})
    calls = []

    def fake_summary(case_data, counts, source_text):
        calls.append((case_data["id"], counts["documents"], source_text))
        return {"english": "cached English", "gujarati": "કેશ્ડ ગુજરાતી"}

    monkeypatch.setattr(analysis, "case_summary", fake_summary)

    first = analysis.overview(case["id"])
    second = analysis.overview(case["id"])

    assert first["summary_cached"] is False
    assert second["summary_cached"] is True
    assert len(calls) == 1

    # A changed source chunk changes the fingerprint and forces regeneration.
    analysis.db.execute(
        "INSERT INTO chunks(id,case_id,document_id,page_number,text,normalized_text,language,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        ("chunk-cache", case["id"], "doc-cache", 1, "New source text", "New source text", "english", "{}"),
    )
    third = analysis.overview(case["id"])
    assert third["summary_cached"] is False
    assert len(calls) == 2
