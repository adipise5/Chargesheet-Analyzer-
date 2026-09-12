from __future__ import annotations

import math
import re
from collections import Counter


def tokens(text: str) -> list[str]:
    values = re.findall(r"[\w\u0A80-\u0AFF]+", text.casefold())
    normalized = []
    for value in values:
        if value.isascii() and len(value) > 5 and value.endswith("es"):
            value = value[:-2]
        elif value.isascii() and len(value) > 4 and value.endswith("s") and not value.endswith("ss"):
            value = value[:-1]
        normalized.append(value)
    return normalized


class LexicalRetriever:
    def retrieve(self, question: str, chunks: list[dict], limit: int = 12) -> list[dict]:
        query = Counter(tokens(question))
        results = []
        for chunk in chunks:
            body = Counter(tokens(chunk["normalized_text"]))
            matched = sum(min(count, body.get(term, 0)) for term, count in query.items())
            score = matched / math.sqrt(max(1, sum(body.values())))
            if score:
                results.append({**chunk, "score": score, "retrieval_method": "lexical"})
        return sorted(results, key=lambda row: row["score"], reverse=True)[:limit]
