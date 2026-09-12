from __future__ import annotations

import re


def useful_native_text(text: str, min_characters: int = 40) -> bool:
    meaningful = re.sub(r"\s+", "", text or "")
    alpha_numeric = sum(ch.isalnum() or "\u0A80" <= ch <= "\u0AFF" for ch in meaningful)
    return len(meaningful) >= min_characters and alpha_numeric / max(len(meaningful), 1) >= 0.45


def extract_native_page(page) -> tuple[str, list[dict]]:
    text = page.get_text("text", sort=True)
    blocks = []
    for index, block in enumerate(page.get_text("blocks", sort=True)):
        x0, y0, x1, y1, value = block[:5]
        if value.strip():
            blocks.append({"block_id": f"native-{index}", "bounding_box": [x0, y0, x1, y1],
                           "text": value.strip(), "confidence": 100.0})
    return text, blocks

