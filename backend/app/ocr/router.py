from __future__ import annotations

from app.ingestion.native_text import useful_native_text
from app.ingestion.page_classifier import classify_page, detect_language
from .base import OCRResult


class DigitalPDFProvider:
    def extract_page(self, page) -> OCRResult:
        from app.ingestion.native_text import extract_native_page
        text, raw_blocks = extract_native_page(page)
        from .base import OCRBlock
        blocks = [OCRBlock(block_id=b["block_id"], text=b["text"], confidence=100,
                           bounding_box=tuple(int(v) for v in b["bounding_box"])) for b in raw_blocks]
        return OCRResult(text=text, confidence=100, engine="native_pdf", blocks=blocks,
                         language=detect_language(text))

    def extract_region(self, page, bounding_box) -> OCRResult:
        text = page.get_text("text", clip=bounding_box)
        return OCRResult(text=text, confidence=100, engine="native_pdf", language=detect_language(text))


class OCRRouter:
    def __init__(self, digital, tesseract, vision=None, threshold: float = 70):
        self.digital = digital
        self.tesseract = tesseract
        self.vision = vision
        self.threshold = threshold

    def route(self, page, image_path=None) -> tuple[OCRResult, OCRResult | None, str]:
        native = self.digital.extract_page(page)
        if useful_native_text(native.text):
            return native, None, "accepted"
        if image_path is None:
            raise ValueError("A rendered image is required for scanned pages")
        result = self.tesseract.extract_page(image_path)
        category = classify_page(result.text, result.confidence, result.low_confidence_word_ratio)
        needs_review = result.confidence < self.threshold or category != "printed"
        vision_result = None
        if needs_review and self.vision is not None:
            try:
                vision_result = self.vision.extract_page(image_path)
            except Exception:
                # Local model absence is surfaced by system health; OCR remains reviewable.
                vision_result = None
        return result, vision_result, "needs_review" if needs_review else "accepted"

