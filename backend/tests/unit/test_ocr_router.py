from app.ocr.base import OCRResult
from app.ocr.router import OCRRouter


class Provider:
    def __init__(self, result): self.result = result
    def extract_page(self, _): return self.result


class Page:
    pass


def test_native_text_bypasses_ocr():
    native = OCRResult("A long native page " * 8, 100, "native_pdf", language="english")
    router = OCRRouter(Provider(native), Provider(OCRResult("should not run", 10, "ocr")))
    result, candidate, status = router.route(Page())
    assert result.engine == "native_pdf"
    assert candidate is None and status == "accepted"


def test_low_confidence_ocr_is_reviewable(tmp_path):
    native = OCRResult("", 100, "native_pdf")
    ocr = OCRResult("uncertain words", 42, "tesseract/guj+eng", low_confidence_word_ratio=.6)
    vision = OCRResult("[UNCLEAR] words", 0, "ollama_vision_candidate")
    router = OCRRouter(Provider(native), Provider(ocr), Provider(vision), threshold=70)
    result, candidate, status = router.route(Page(), tmp_path / "page.png")
    assert result is ocr and candidate is vision and status == "needs_review"

