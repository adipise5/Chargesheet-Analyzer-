from __future__ import annotations

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    denom = math.sqrt(sum(v*v for v in left)) * math.sqrt(sum(v*v for v in right))
    return sum(a*b for a, b in zip(left, right)) / denom if denom else 0.0

