from __future__ import annotations

import re
import uuid

from app.extraction.date_utils import GUJARATI_DIGITS, normalize_date

DATE = re.compile(r"(?<!\w)([0-9૦૧૨૩૪૫૬૭૮૯]{1,4}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,2}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,4})(?:\s+(?:at\s+)?([0-9૦૧૨૩૪૫૬૭૮૯]{1,2}:[0-9૦૧૨૩૪૫૬૭૮૯]{2}))?(?!\w)", re.I)


def _event_description(text: str, match: re.Match[str], normalized_date: str) -> tuple[str, bool, float]:
    """Return a readable event label and a conservative date-quality flag."""
    before = text[max(0, match.start() - 220):match.start()]
    compact_before = " ".join(before.split())
    field_labels = (
        (r"date\s+of\s+arrest", "Date of arrest"),
        (r"date\s+of\s+sending\s+to\s+court", "Date sent to court"),
        (r"date\s+of\s+release\s+on\s+bail", "Date of release on bail"),
        (r"final\s+report\s*/?\s*charge\s*sheet\s+no\.?\s*:\s*[^\n]*\s+\d{1,2}[.)]?\s+date", "Final report / charge sheet date"),
    )
    matched_fields = []
    for pattern, label in field_labels:
        found = list(re.finditer(pattern, compact_before, re.I))
        if found:
            matched_fields.append((found[-1].start(), label))
    if matched_fields:
        return max(matched_fields)[1], False, 0.92

    # Keep narrative events useful without presenting a large form row as the
    # event name. The exact date is still retained separately in metadata.
    start = max(text.rfind("\n", 0, match.start()), text.rfind(".", 0, match.start())) + 1
    end_candidates = [index for index in (text.find("\n", match.end()), text.find(".", match.end())) if index >= 0]
    end = min(end_candidates) if end_candidates else min(len(text), match.end() + 120)
    sentence = " ".join(text[start:end].split())
    if sentence:
        return sentence[:160], True, 0.84
    return f"Date recorded in source ({normalized_date})", True, 0.8


def extract_events(text: str, chunk_id: str) -> list[dict]:
    events = []
    for match in DATE.finditer(text):
        raw_date = match.group(1)
        normalized_date = normalize_date(raw_date)
        if not normalized_date:
            continue
        raw_time = match.group(2)
        time = raw_time.translate(GUJARATI_DIGITS) if raw_time else None
        value = raw_date + (f" {raw_time}" if raw_time else "")
        label, date_uncertain, confidence = _event_description(text, match, normalized_date)
        events.append({
            "id": f"event_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + value + label).hex[:12]}",
            "kind": "Event", "subtype": "dated_event", "label": label,
            "confidence": confidence, "data": {"date": raw_date, "normalized_date": normalized_date, "time": time,
                                                   "date_uncertain": date_uncertain, "source_chunk": chunk_id},
        })
    return events[:20]

