from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\u200c", "").replace("\u200d", "")
    value = re.sub(r"[\t\r ]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize_entity(value: str) -> str:
    value = normalize_text(value).casefold()
    return re.sub(r"[^\w\u0A80-\u0AFF]+", "", value)


def resolution_decision(left: dict, right: dict) -> tuple[str | None, float]:
    """Conservative matcher: exact context identifiers can merge; names alone cannot."""
    ln, rn = normalize_entity(left.get("label", "")), normalize_entity(right.get("label", ""))
    if not ln or not rn:
        return None, 0.0
    phone_match = bool(set(left.get("phones", [])) & set(right.get("phones", [])))
    address_match = bool(set(left.get("addresses", [])) & set(right.get("addresses", [])))
    ratio = SequenceMatcher(None, ln, rn).ratio()
    if ln == rn and (phone_match or address_match):
        return "SAME_AS", 0.98
    if ratio >= 0.84 or phone_match:
        return "POSSIBLY_SAME_AS", min(0.9, 0.62 + ratio * 0.25 + (0.08 if phone_match else 0))
    return None, ratio

