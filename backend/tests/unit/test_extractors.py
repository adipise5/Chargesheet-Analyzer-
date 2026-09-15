from app.extraction.entity_extractor import extract_entities
from app.extraction.event_extractor import extract_events


def test_gujarati_section_number_is_extracted_as_legal_entity():
    entities = extract_entities("આરોપ કલમ ૨૨૩ હેઠળ છે", "chunk-1")
    assert any(item["kind"] == "LegalSection" and "૨૨૩" in item["label"] for item in entities)


def test_english_legal_sections_accept_colons_and_number_lists():
    entities = extract_entities("IN THE COURT OF SESSIONS. Section: 300 and Ss. 302, 304A and 34 IPC", "chunk-legal")
    labels = {item["label"] for item in entities if item["kind"] == "LegalSection"}
    assert all(any(number in label for label in labels) for number in ("300", "302", "304A", "34"))


def test_gujarati_date_is_normalized_and_time_is_ascii():
    events = extract_events("ઘટના ૧૩/૦૩/૨૦૨૬ ૧૪:૩૦", "chunk-1")
    assert len(events) == 1
    assert events[0]["data"]["normalized_date"] == "2026-03-13"
    assert events[0]["data"]["time"] == "14:30"


def test_date_field_label_uses_the_nearest_form_heading():
    text = "13. Date of Arrest : 17/12/2014 15. Date of sending to Court : 18/12/2014"
    events = extract_events(text, "chunk-fields")
    assert [event["label"] for event in events] == ["Date of arrest", "Date sent to court"]
    assert all(event["data"]["date_uncertain"] is False for event in events)
