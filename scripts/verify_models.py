"""Verify the configured localhost Ollama models without printing model input/output."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.embedding_service import OllamaEmbeddingProvider  # noqa: E402
from app.services.ollama_service import OllamaService  # noqa: E402


def main() -> None:
    service = OllamaService()
    health = service.health()
    if not health["available"] or health["missing"]:
        raise SystemExit(f"Required local models are unavailable: {health.get('missing')}")
    vectors = OllamaEmbeddingProvider().embed(["synthetic local multilingual verification"])
    if len(vectors) != 1 or not vectors[0]:
        raise SystemExit("Embedding response is empty")
    answer = service.answer("Return only the word READY. Do not add explanation.")
    if not answer:
        raise SystemExit("Local LLM response is empty")
    print(f"Local models verified: LLM={service.config.llm_model}, embedding={service.config.embedding_model}, dimensions={len(vectors[0])}")


if __name__ == "__main__":
    main()
