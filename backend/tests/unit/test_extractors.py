from app.extraction.entity_extractor import extract_entities
from app.extraction.event_extractor import extract_events


def test_gujarati_section_number_is_extracted_as_legal_entity():
    entities = extract_entities("આરોપ કલમ ૨૨૩ હેઠળ છે", "chunk-1")
    assert any(item["kind"] == "LegalSection" and "૨૨૩" in item["label"] for item in entities)


def test_gujarati_date_is_normalized_and_time_is_ascii():
    events = extract_events("ઘટના ૧૩/૦૩/૨૦૨૬ ૧૪:૩૦", "chunk-1")
    assert len(events) == 1
    assert events[0]["data"]["normalized_date"] == "2026-03-13"
    assert events[0]["data"]["time"] == "14:30"
