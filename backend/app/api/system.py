import json
import hashlib

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.runtime_mode import is_read_only_demo, require_writable
from app.storage.sqlite import db, now_iso

router = APIRouter(prefix="/api/system", tags=["system"])


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=200)
    target: str = Field(pattern="^(english|gujarati)$")


def _translation_candidates(value: object) -> list[str]:
    """Flatten the small set of JSON shapes local models commonly emit.

    The requested contract is a flat array, but compact local models sometimes
    wrap the array once or include the source array beside the translation.
    Only strings are retained; arbitrary objects are never rendered in the UI.
    """
    if isinstance(value, str):
        return [value.strip()]
    if isinstance(value, list):
        candidates: list[str] = []
        for item in value:
            candidates.extend(_translation_candidates(item))
        return candidates
    return []


def _looks_like_target(text: str, target: str) -> bool:
    if target == "gujarati":
        return any("\u0A80" <= char <= "\u0AFF" for char in text)
    return not any("\u0A80" <= char <= "\u0AFF" for char in text)


def _parse_translation_response(raw: str, source_texts: list[str], target: str) -> list[str] | None:
    """Parse strict output and tolerate one unambiguous Qwen wrapper.

    Qwen occasionally omits the final bracket of an outer array while keeping
    each inner one-item array valid. Recovering those inner arrays is safe here
    because the parser still selects only strings in the requested script and
    never renders raw JSON or arbitrary model objects.
    """
    start, end = raw.find("["), raw.rfind("]")
    if start < 0 or end <= start:
        return None
    payload: object | None = None
    try:
        payload = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        nested: list[list[object]] = []
        for index, char in enumerate(raw[start:end + 1]):
            if char != "[":
                continue
            try:
                candidate, _ = decoder.raw_decode(raw[start:end + 1], index)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, list):
                nested.append(candidate)
        if not nested:
            return None
        candidates = [text for item in nested for text in _translation_candidates(item)]
    else:
        if not isinstance(payload, list):
            return None
        candidates = _translation_candidates(payload)
    if isinstance(payload, list) and len(payload) == len(source_texts) and all(isinstance(item, str) for item in payload):
        candidates = [item.strip() for item in payload]
    selected: list[str] = []
    used: set[int] = set()
    for source in source_texts:
        source_clean = source.strip()
        preferred = [
            index for index, candidate in enumerate(candidates)
            if index not in used and candidate and candidate != source_clean and _looks_like_target(candidate, target)
        ]
        fallback = [
            index for index, candidate in enumerate(candidates)
            if index not in used and candidate and candidate != source_clean
        ]
        index = (preferred or fallback or [index for index in range(len(candidates)) if index not in used])
        if not index:
            return None
        chosen = index[0]
        used.add(chosen)
        selected.append(candidates[chosen])
    return selected if len(selected) == len(source_texts) else None


@router.post("/translate")
def translate(payload: TranslationRequest):
    if payload.target == "english":
        instruction = "Translate each item from Gujarati (including mixed Gujarati-English text) into natural professional English. Preserve names, case numbers, dates, section numbers, citations, and uncertainty exactly."
    else:
        instruction = "Translate each item into clear, natural, formal Gujarati suitable for a police case-review interface. Preserve the meaning exactly: allegations must remain allegations, and do not turn uncertainty into a fact. Transliterate proper names rather than translating them semantically. Keep legal abbreviations, case numbers, dates, section numbers, citations, and technical terms such as CrPC and IPC unchanged where that is clearer."
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
    # The hosted snapshot intentionally has no model runtime. Its translations
    # must be prepared locally before deployment; an uncached value is returned
    # unchanged rather than making a network request or pretending it was
    # translated.
    if is_read_only_demo():
        for index in missing_indexes:
            result[index] = payload.texts[index]
        return {"translations": [value or "" for value in result], "fallback": bool(missing_indexes), "cache_only": True}
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
        translated = _parse_translation_response(raw, missing_texts, payload.target)
        if translated is None:
            raise ValueError("translation response shape mismatch")
        for index, translated_text in zip(missing_indexes, translated):
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
    require_writable()
    from app.services.purge_service import purge_all_data
    return {"status": "purged", "removed": purge_all_data()}


@router.get("/health")
def health():
    if is_read_only_demo():
        return {"status": "ok", "mode": "render_demo", "read_only": True, "models_required": False,
                "offline_policy": "read-only precomputed snapshot", "hardware_memory_gb": None,
                "llm_model": None, "embedding_model": None,
                "ollama": {"available": False, "models": [], "missing": [], "disabled": True},
                "tesseract": {"available": False, "message": "Disabled in hosted snapshot mode"},
                "neo4j": {"available": False, "mode": "sqlite-system-of-record"}}
    from app.core.model_config import ModelConfig
    from app.ocr.tesseract_provider import TesseractOCRProvider
    from app.services.ollama_service import OllamaService
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
    return {"status": "ok", "mode": "local", "read_only": False, "models_required": True, "offline_policy": "localhost/private-only", "hardware_memory_gb": config.memory_gb,
            "llm_model": config.llm_model, "embedding_model": config.embedding_model,
            "ollama": ollama, "tesseract": {"available": tess_ok, "message": tess_message}, "neo4j": neo4j}
