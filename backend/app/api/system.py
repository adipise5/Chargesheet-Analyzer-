import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.model_config import ModelConfig
from app.ocr.tesseract_provider import TesseractOCRProvider
from app.services.ollama_service import OllamaService
from app.services.purge_service import purge_all_data

router = APIRouter(prefix="/api/system", tags=["system"])


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=60)
    target: str = Field(pattern="^(english|gujarati)$")


@router.post("/translate")
def translate(payload: TranslationRequest):
    if payload.target == "english":
        instruction = "Translate each item from Gujarati (including mixed Gujarati-English text) into natural professional English. Preserve names, case numbers, dates, section numbers, citations, and uncertainty exactly."
    else:
        instruction = "Translate each item into natural professional Gujarati script. Preserve names, case numbers, dates, section numbers, citations, and uncertainty exactly."
    prompt = f"""{instruction}
Return ONLY a JSON array of strings in the same order and length as the input.
Do not summarize, explain, or add facts.
INPUT:\n{json.dumps(payload.texts, ensure_ascii=False)}"""
    try:
        from app.services.ollama_service import OllamaService
        raw = OllamaService().answer(prompt)
        start, end = raw.find("["), raw.rfind("]")
        translated = json.loads(raw[start:end + 1]) if start >= 0 and end > start else None
        if not isinstance(translated, list) or len(translated) != len(payload.texts):
            raise ValueError("translation response shape mismatch")
        return {"translations": [str(value) for value in translated]}
    except Exception:
        # Never hide source material when the local model is unavailable.
        return {"translations": payload.texts, "fallback": True}


@router.delete("/purge")
def purge_data():
    """Permanently erase all local case and judgment runtime data."""
    return {"status": "purged", "removed": purge_all_data()}


@router.get("/health")
def health():
    config = ModelConfig.from_env()
    tess_ok, tess_message = TesseractOCRProvider().available()
    ollama = OllamaService(config).health()
    neo4j = {"available": False, "mode": "sqlite-system-of-record"}
    if settings.neo4j_enabled or settings.require_neo4j:
        try:
            from neo4j import GraphDatabase
            auth = (settings.neo4j_user, settings.neo4j_password) if settings.neo4j_password else None
            with GraphDatabase.driver(settings.neo4j_uri, auth=auth) as driver:
                driver.verify_connectivity()
            neo4j = {"available": True, "mode": "local-projection"}
        except Exception as exc:
            neo4j["error"] = str(exc)
    return {"status": "ok", "offline_policy": "localhost/private-only", "hardware_memory_gb": config.memory_gb,
            "llm_model": config.llm_model, "embedding_model": config.embedding_model,
            "ollama": ollama, "tesseract": {"available": tess_ok, "message": tess_message}, "neo4j": neo4j}
