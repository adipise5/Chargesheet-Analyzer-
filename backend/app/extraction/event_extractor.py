from __future__ import annotations

import re
import uuid

from app.extraction.date_utils import GUJARATI_DIGITS, normalize_date

DATE = re.compile(r"(?<!\w)([0-9૦૧૨૩૪૫૬૭૮૯]{1,4}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,2}\s*[/.-]\s*[0-9૦૧૨૩૪૫૬૭૮૯]{1,4})(?:\s+(?:at\s+)?([0-9૦૧૨૩૪૫૬૭૮૯]{1,2}:[0-9૦૧૨૩૪૫૬૭૮૯]{2}))?(?!\w)", re.I)


def extract_events(text: str, chunk_id: str) -> list[dict]:
    events = []
    for match in DATE.finditer(text):
        context = text[max(0, match.start()-50): min(len(text), match.end()+90)].replace("\n", " ").strip()
        raw_date = match.group(1)
        normalized_date = normalize_date(raw_date)
        if not normalized_date:
            continue
        raw_time = match.group(2)
        time = raw_time.translate(GUJARATI_DIGITS) if raw_time else None
        value = raw_date + (f" {raw_time}" if raw_time else "")
        events.append({
            "id": f"event_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + value + context).hex[:12]}",
            "kind": "Event", "subtype": "dated_event", "label": context[:140],
            "confidence": 0.78, "data": {"date": raw_date, "normalized_date": normalized_date, "time": time, "source_chunk": chunk_id},
        })
    return events[:20]

