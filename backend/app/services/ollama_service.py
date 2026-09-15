from __future__ import annotations

import json
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.model_config import ModelConfig
from app.core.runtime_mode import is_read_only_demo
from .llm_provider import LLMProvider

T = TypeVar("T", bound=BaseModel)


class LocalModelUnavailable(RuntimeError):
    pass


class OllamaService(LLMProvider):
    def __init__(self, config: ModelConfig | None = None):
        if is_read_only_demo():
            raise LocalModelUnavailable("Model inference is disabled in the hosted demo")
        self.config = config or ModelConfig.from_env()

    def health(self) -> dict:
        try:
            with httpx.Client(timeout=2, trust_env=False) as client:
                response = client.get(f"{self.config.ollama_base_url}/api/tags")
                response.raise_for_status()
                names = [model.get("name") for model in response.json().get("models", [])]
            required = [self.config.llm_model, self.config.embedding_model]
            def installed(required_name: str) -> bool:
                return any(name == required_name or (":" not in required_name and name.startswith(required_name + ":")) for name in names if name)
            return {"available": True, "models": names, "missing": [m for m in required if not installed(m)]}
        except Exception as exc:
            return {"available": False, "models": [], "missing": [self.config.llm_model, self.config.embedding_model], "error": str(exc)}

    def structured(self, prompt: str, schema: type[T], temperature: float = 0.1) -> T:
        correction = ""
        for attempt in range(2):
            payload = {
                "model": self.config.llm_model,
                "stream": False,
                "think": False,
                "format": schema.model_json_schema(),
                "options": {"temperature": temperature, "num_ctx": 12288, "num_predict": 2048},
                "messages": [{"role": "user", "content": prompt + correction}],
            }
            try:
                with httpx.Client(timeout=180, trust_env=False) as client:
                    response = client.post(f"{self.config.ollama_base_url}/api/chat", json=payload)
                    response.raise_for_status()
                return schema.model_validate_json(response.json()["message"]["content"])
            except (httpx.HTTPError, KeyError) as exc:
                raise LocalModelUnavailable(f"Local Ollama request failed: {exc}") from exc
            except (ValidationError, json.JSONDecodeError) as exc:
                if attempt:
                    raise ValueError("Local model returned invalid structured JSON after one correction") from exc
                correction = "\nYour previous response failed schema validation. Return only corrected JSON."
        raise AssertionError("unreachable")

    def vision(self, prompt: str, image_base64: str) -> str:
        payload = {"model": self.config.llm_model, "stream": False, "think": False,
                   "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 4096},
                   "messages": [{"role": "user", "content": prompt, "images": [image_base64]}]}
        try:
            with httpx.Client(timeout=240, trust_env=False) as client:
                response = client.post(f"{self.config.ollama_base_url}/api/chat", json=payload)
                response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except Exception as exc:
            raise LocalModelUnavailable(f"Local vision model unavailable: {exc}") from exc

    def _answer(self, prompt: str, *, max_output_tokens: int = 768,
                fail_on_truncation: bool = False, append_limit_notice: bool = True) -> str:
        payload = {"model": self.config.llm_model, "stream": False, "think": False,
                   "options": {"temperature": 0.1, "num_ctx": 12288, "num_predict": max_output_tokens},
                   "messages": [{"role": "user", "content": prompt}]}
        try:
            with httpx.Client(timeout=180, trust_env=False) as client:
                response = client.post(f"{self.config.ollama_base_url}/api/chat", json=payload)
                response.raise_for_status()
            result = response.json()
            content = result["message"]["content"].strip()
            if not content:
                raise LocalModelUnavailable("Local model returned an empty answer")
            if result.get("done_reason") == "length" and fail_on_truncation:
                raise LocalModelUnavailable("Local model response exceeded the bounded response length")
            if result.get("done_reason") == "length" and append_limit_notice:
                content += "\n\nThe model reached its response limit. Ask a narrower question for more detail."
            return content
        except LocalModelUnavailable:
            raise
        except Exception as exc:
            raise LocalModelUnavailable(f"Local model unavailable: {exc}") from exc

    def answer(self, prompt: str) -> str:
        """Return a model answer while preserving the legacy soft limit notice."""
        return self._answer(prompt)

    def answer_bounded(self, prompt: str, max_output_tokens: int = 520) -> str:
        """Return only a complete answer; truncated model output is rejected.

        Legal-research and case Q&A callers use this path so an incomplete
        response is replaced by a source-only fallback instead of being shown
        as if it were a finished conclusion.
        """
        return self._answer(prompt, max_output_tokens=max_output_tokens,
                            fail_on_truncation=True, append_limit_notice=False)
