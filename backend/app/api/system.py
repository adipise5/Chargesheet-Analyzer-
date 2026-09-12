from fastapi import APIRouter

from app.core.config import settings
from app.core.model_config import ModelConfig
from app.ocr.tesseract_provider import TesseractOCRProvider
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/api/system", tags=["system"])


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
