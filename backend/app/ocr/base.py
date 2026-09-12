from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OCRBlock:
    block_id: str
    text: str
    confidence: float
    bounding_box: tuple[int, int, int, int]


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str
    blocks: list[OCRBlock] = field(default_factory=list)
    language: str = "unknown"
    low_confidence_word_ratio: float = 0.0


class OCRProvider(ABC):
    @abstractmethod
    def extract_page(self, image_path: Path) -> OCRResult:
        raise NotImplementedError

    @abstractmethod
    def extract_region(self, image_path: Path, bounding_box: tuple[int, int, int, int]) -> OCRResult:
        raise NotImplementedError

