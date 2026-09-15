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


def test_cross_case_analytics_aggregates_non_demo_records():
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

    assert global_summary()["total_cases"] == 2
    assert global_summary()["total_accused"] == 2
    assert crime_type_distribution() == [{"section": "IPC 302", "count": 1}]
    assert crime_hotspots() == [{"station": "North", "count": 2}]
    assert set(tuple(item.values()) for item in case_status_distribution()) == {("created", 1), ("ready", 1)}
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


def test_date_normalization_handles_gujarati_and_year_first_formats():
    assert normalize_date("૧૩/૦૩/૨૦૨૬") == "2026-03-13"
    assert normalize_date("13.03.2026") == "2026-03-13"
    assert normalize_date("2026-03-13") == "2026-03-13"
    assert normalize_date("31/02/2026") is None
