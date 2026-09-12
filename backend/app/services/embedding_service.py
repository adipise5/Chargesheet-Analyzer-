from __future__ import annotations

import httpx

from app.core.model_config import ModelConfig
from .ollama_service import LocalModelUnavailable


class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig.from_env()

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            with httpx.Client(timeout=180, trust_env=False) as client:
                response = client.post(f"{self.config.ollama_base_url}/api/embed",
                                       json={"model": self.config.embedding_model, "input": texts})
                response.raise_for_status()
            return response.json()["embeddings"]
        except Exception as exc:
            raise LocalModelUnavailable(f"Local embedding model unavailable: {exc}") from exc

