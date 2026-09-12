from __future__ import annotations


def detect_language(text: str) -> str:
    gujarati = sum("\u0A80" <= char <= "\u0AFF" for char in text)
    english = sum(char.isascii() and char.isalpha() for char in text)
    if gujarati and english and min(gujarati, english) / max(gujarati, english) > 0.12:
        return "mixed"
    if gujarati:
        return "gujarati"
    if english:
        return "english"
    return "unknown"


def classify_page(text: str, ocr_confidence: float, low_confidence_word_ratio: float = 0) -> str:
    if ocr_confidence < 45 or low_confidence_word_ratio > 0.45:
        return "handwritten_or_low_confidence"
    if ocr_confidence < 70:
        return "mixed_or_uncertain"
    return "printed"

