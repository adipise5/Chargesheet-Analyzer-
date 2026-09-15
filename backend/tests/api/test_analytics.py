from app.services.analytics_service import (
    case_status_distribution,
    crime_hotspots,
    crime_type_distribution,
    entity_network,
    evidence_profile,
    findings_summary,
    global_summary,
    temporal_distribution,
)
from app.services.case_service import create_case
from app.storage.sqlite import db
from app.extraction.date_utils import normalize_date


def test_cross_case_analytics_aggregates_case_records_and_excludes_only_references():
    first = create_case({"case_number": "ANALYTICS-1", "police_station": "North"})
    second = create_case({"case_number": "ANALYTICS-2", "police_station": "North"})
    demo = create_case({"case_number": "DEMO-ONLY", "police_station": "South"}, is_demo=True)

    for case_id, accused in ((first["id"], "A-1"), (second["id"], "A-1"), (demo["id"], "DEMO") ):
        db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
                   (f"accused-{case_id}", case_id, "Accused", "accused", accused, "{}", 0.9))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("section-1", first["id"], "LegalSection", "legal_section", "IPC 302", "{}", 0.9))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("evidence-1", first["id"], "Evidence", "forensic", "DNA sample", "{}", 0.7))
    db.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
               ("finding-1", first["id"], "contradiction", "{}"))
    db.execute("UPDATE cases SET status='ready' WHERE id=?", (first["id"],))

    assert global_summary()["total_cases"] == 3
    assert global_summary()["total_accused"] == 3
    assert crime_type_distribution() == [{"section": "IPC 302", "count": 1}]
    assert crime_hotspots() == [{"station": "North", "count": 2}, {"station": "South", "count": 1}]
    assert set(tuple(item.values()) for item in case_status_distribution()) == {("created", 1), ("ready", 2)}
    assert evidence_profile() == [{"type": "forensic", "count": 1}]
    assert findings_summary() == [{"type": "contradiction", "count": 1}]
    assert {item["label"] for item in entity_network()} == {"A-1"}
    assert temporal_distribution()


def test_temporal_analytics_merges_ascii_and_gujarati_dates():
    case = create_case({"case_number": "DATE-NORMALIZATION", "police_station": "Training"})
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("event-ascii", case["id"], "Event", "dated_event", "ASCII date", '{"date":"13/03/2026"}', 0.9))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("event-gujarati", case["id"], "Event", "dated_event", "Gujarati date", '{"date":"૧૩/૦૩/૨૦૨૬"}', 0.9))

    result = temporal_distribution()
    assert {item["month"] for item in result} == {"2026-03", case["created_at"][:7]}
    march = next(item for item in result if item["month"] == "2026-03")
    assert march["crime_events"] == 2


def test_public_judgment_records_are_excluded_from_incident_analytics_by_default():
    incident = create_case({"case_number": "INCIDENT-SCOPE", "police_station": "Incident Station"})
    reference = create_case({"case_number": "REFERENCE-SCOPE", "police_station": "Reference Court",
                             "record_type": "public_judgment"})
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("incident-section", incident["id"], "LegalSection", "legal_section", "IPC 302", "{}", 1.0))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("reference-section", reference["id"], "LegalSection", "legal_section", "Section 438", "{}", 1.0))
    db.execute("INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
               ("reference-event", reference["id"], "Event", "dated_event", "Judgment date",
                '{"normalized_date":"2024-01-02"}', 1.0))

    default = global_summary()
    included = global_summary(include_reference_records=True)
    assert default["total_cases"] == 1
    assert default["reference_cases"] == 1
    assert included["total_cases"] == 2
    assert crime_type_distribution() == [{"section": "IPC 302", "count": 1}]
    assert {item["section"] for item in crime_type_distribution(True)} == {"IPC 302", "Section 438"}
    assert all(item["month"] != "2024-01" for item in temporal_distribution())
    assert any(item["month"] == "2024-01" for item in temporal_distribution(True))


def test_date_normalization_handles_gujarati_and_year_first_formats():
    assert normalize_date("૧૩/૦૩/૨૦૨૬") == "2026-03-13"
    assert normalize_date("13.03.2026") == "2026-03-13"
    assert normalize_date("2026-03-13") == "2026-03-13"
    assert normalize_date("31/02/2026") is None
