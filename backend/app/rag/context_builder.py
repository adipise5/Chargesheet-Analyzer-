from __future__ import annotations


def build_context(results: list[dict], max_characters: int = 42000) -> tuple[str, list[dict]]:
    parts, citations, size = [], [], 0
    for result in results:
        label = f"S{len(citations) + 1}"
        block = f"[{label}]\n{result['text'].strip()}"
        if size + len(block) > max_characters:
            break
        parts.append(block)
        citations.append({"document_id": result["document_id"], "page": result["page_number"],
                          "chunk_id": result["id"], "label": f"{label}: {result.get('document_label', 'Document')}"})
        size += len(block)
    return "\n\n".join(parts), citations

