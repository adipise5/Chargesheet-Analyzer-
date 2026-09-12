from __future__ import annotations

from pathlib import Path

from app.ingestion.page_classifier import detect_language
from .base import OCRBlock, OCRProvider, OCRResult
from .preprocessing import preprocess_image


class OCRConfigurationError(RuntimeError):
    pass


class TesseractOCRProvider(OCRProvider):
    def __init__(self, languages: str = "guj+eng"):
        self.languages = languages

    def available(self) -> tuple[bool, str]:
        try:
            import pytesseract
            languages = set(pytesseract.get_languages(config=""))
            missing = set(self.languages.split("+")) - languages
            if missing:
                return False, f"Missing Tesseract language data: {', '.join(sorted(missing))}"
            return True, "ready"
        except Exception as exc:
            return False, f"Tesseract is unavailable: {exc}"

    def extract_page(self, image_path: Path) -> OCRResult:
        return self._extract(preprocess_image(image_path))

    def extract_region(self, image_path: Path, bounding_box: tuple[int, int, int, int]) -> OCRResult:
        image = preprocess_image(image_path).crop(bounding_box)
        return self._extract(image)

    def _extract(self, image) -> OCRResult:
        import pytesseract
        available, message = self.available()
        if not available:
            raise OCRConfigurationError(message)
        data = pytesseract.image_to_data(
            image, lang=self.languages, config="--oem 1 --psm 3", output_type=pytesseract.Output.DICT
        )
        blocks: list[OCRBlock] = []
        words: list[str] = []
        confidences: list[float] = []
        low = 0
        for index, raw in enumerate(data["text"]):
            word = raw.strip()
            try:
                confidence = float(data["conf"][index])
            except (TypeError, ValueError):
                confidence = -1
            if not word or confidence < 0:
                continue
            words.append(word)
            confidences.append(confidence)
            low += int(confidence < 50)
            blocks.append(OCRBlock(
                block_id=f"ocr-{index}", text=word, confidence=confidence,
                bounding_box=(int(data["left"][index]), int(data["top"][index]),
                              int(data["width"][index]), int(data["height"][index])),
            ))
        text = " ".join(words)
        return OCRResult(
            text=text,
            confidence=sum(confidences) / len(confidences) if confidences else 0.0,
            engine=f"tesseract/{self.languages}",
            blocks=blocks,
            language=detect_language(text),
            low_confidence_word_ratio=low / len(confidences) if confidences else 1.0,
        )

