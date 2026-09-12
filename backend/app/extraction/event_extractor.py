from __future__ import annotations

import re
import uuid

DATE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})(?:\s+(?:at\s+)?(\d{1,2}:\d{2}))?\b", re.I)


def extract_events(text: str, chunk_id: str) -> list[dict]:
    events = []
    for match in DATE.finditer(text):
        context = text[max(0, match.start()-50): min(len(text), match.end()+90)].replace("\n", " ").strip()
        value = match.group(1) + (f" {match.group(2)}" if match.group(2) else "")
        events.append({
            "id": f"event_{uuid.uuid5(uuid.NAMESPACE_URL, chunk_id + value + context).hex[:12]}",
            "kind": "Event", "subtype": "dated_event", "label": context[:140],
            "confidence": 0.78, "data": {"date": match.group(1), "time": match.group(2), "source_chunk": chunk_id},
        })
    return events[:20]

