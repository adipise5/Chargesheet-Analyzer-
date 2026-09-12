import json
import hashlib

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.model_config import ModelConfig
from app.ocr.tesseract_provider import TesseractOCRProvider
from app.services.ollama_service import OllamaService
from app.services.purge_service import purge_all_data
from app.storage.sqlite import db, now_iso

router = APIRouter(prefix="/api/system", tags=["system"])


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=200)
    target: str = Field(pattern="^(english|gujarati)$")


@router.post("/translate")
def translate(payload: TranslationRequest):
    if payload.target == "english":
        instruction = "Translate each item from Gujarati (including mixed Gujarati-English text) into natural professional English. Preserve names, case numbers, dates, section numbers, citations, and uncertainty exactly."
    else:
        instruction = "Translate each item into natural professional Gujarati script. Preserve names, case numbers, dates, section numbers, citations, and uncertainty exactly."
    def text_hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    hashes = [text_hash(value) for value in payload.texts]
    placeholders = ",".join("?" for _ in hashes)
    cached_rows = db.all(
        f"SELECT text_hash,translated_text FROM translation_cache WHERE target=? AND text_hash IN ({placeholders})",
        (payload.target, *hashes),
    )
    cached = {row["text_hash"]: row["translated_text"] for row in cached_rows}
    result: list[str | None] = [cached.get(digest) for digest in hashes]
    missing_indexes = [index for index, value in enumerate(result) if value is None]
    # English-only source text is already in the requested language and does
    # not need a model round trip. Gujarati/mixed source still goes through the
    # local model when an English translation is requested.
    for index in missing_indexes[:]:
        if payload.target == "english" and not any("\u0A80" <= char <= "\u0AFF" for char in payload.texts[index]):
            result[index] = payload.texts[index]
            db.execute("INSERT OR REPLACE INTO translation_cache(text_hash,target,source_text,translated_text,created_at) VALUES(?,?,?,?,?)",
                       (hashes[index], payload.target, payload.texts[index], payload.texts[index], now_iso()))
    missing_indexes = [index for index, value in enumerate(result) if value is None]
    if not missing_indexes:
        return {"translations": [value or "" for value in result], "cached": True}
    missing_texts = [payload.texts[index] for index in missing_indexes]
    prompt = f"""{instruction}
Return ONLY a JSON array of strings in the same order and length as the input.
Do not summarize, explain, or add facts.
INPUT:\n{json.dumps(missing_texts, ensure_ascii=False)}"""
    try:
        from app.services.ollama_service import OllamaService
        raw = OllamaService().answer(prompt)
        start, end = raw.find("["), raw.rfind("]")
        translated = json.loads(raw[start:end + 1]) if start >= 0 and end > start else None
        if not isinstance(translated, list) or len(translated) != len(missing_texts):
            raise ValueError("translation response shape mismatch")
        # Small local models occasionally wrap one answer in an extra JSON
        # array. Accept only the unambiguous one-item form; never stringify a
        # list into UI text such as "['translated text']".
        normalized = []
        for value in translated:
            if isinstance(value, str):
                cleaned = value.strip()
                if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
                    cleaned = cleaned[1:-1].strip()
                normalized.append(cleaned)
            elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                normalized.append(value[0].strip())
            else:
                raise ValueError("translation item is not a string")
        for index, translated_text in zip(missing_indexes, normalized):
            result[index] = translated_text
            db.execute("INSERT OR REPLACE INTO translation_cache(text_hash,target,source_text,translated_text,created_at) VALUES(?,?,?,?,?)",
                       (hashes[index], payload.target, payload.texts[index], translated_text, now_iso()))
        return {"translations": [value or "" for value in result], "cached": bool(not cached_rows)}
    except Exception:
        # Never hide source material when the local model is unavailable.
        for index in missing_indexes:
            result[index] = payload.texts[index]
        return {"translations": [value or "" for value in result], "fallback": True}


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
