from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Replaceable boundary for local/internal language and vision inference."""

    @abstractmethod
    def health(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def structured(self, prompt: str, schema: type[T], temperature: float = 0.1) -> T:
        raise NotImplementedError

    @abstractmethod
    def vision(self, prompt: str, image_base64: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def answer(self, prompt: str) -> str:
        raise NotImplementedError

