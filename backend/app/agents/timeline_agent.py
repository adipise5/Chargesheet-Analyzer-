def timeline_from_objects(objects: list[dict], chunks_by_id: dict[str, dict]) -> list[dict]:
    timeline = []
    for item in objects:
        if item["kind"] != "Event":
            continue
        chunk = chunks_by_id.get(item.get("data", {}).get("source_chunk", ""))
        if chunk:
            timeline.append({"id": item["id"], "date": item["data"].get("date"), "normalized_date": item["data"].get("normalized_date"), "time": item["data"].get("time"),
                             "event": item["label"], "category": "investigation", "people": [], "location": None,
                             "confidence": item["confidence"], "uncertain": item["confidence"] < 0.8,
                             "citation": {"document_id": chunk["document_id"], "page": chunk["page_number"], "chunk_id": chunk["id"],
                                          "label": f"Event source — p{chunk['page_number']}"}})
    return sorted(timeline, key=lambda item: (item.get("normalized_date") or "9999-99-99", item.get("time") or "99:99"))

