from __future__ import annotations

import base64
from pathlib import Path

from app.services.ollama_service import OllamaService
from .base import OCRProvider, OCRResult


class VisionOCRVerifier(OCRProvider):
    def __init__(self, service: OllamaService | None = None):
        self.service = service or OllamaService()

    def extract_page(self, image_path: Path) -> OCRResult:
        prompt = (Path(__file__).parents[1] / "prompts" / "vision_transcription.txt").read_text()
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        text = self.service.vision(prompt, encoded)
        return OCRResult(text=text, confidence=0.0, engine="ollama_vision_candidate")

    def extract_region(self, image_path: Path, bounding_box: tuple[int, int, int, int]) -> OCRResult:
        from PIL import Image
        import io
        image = Image.open(image_path).crop(bounding_box)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        prompt = (Path(__file__).parents[1] / "prompts" / "vision_transcription.txt").read_text()
        text = self.service.vision(prompt, base64.b64encode(buffer.getvalue()).decode("ascii"))
        return OCRResult(text=text, confidence=0.0, engine="ollama_vision_candidate")

