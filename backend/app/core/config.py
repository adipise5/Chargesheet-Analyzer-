from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .model_config import ModelConfig, is_approved_local_url


ROOT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    cases_dir: Path = ROOT_DIR / "data" / "cases"
    database_path: Path = ROOT_DIR / "data" / "chargesheet.db"
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_MB", "250")) * 1024 * 1024
    ocr_confidence_threshold: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "70"))
    ocr_workers: int = int(os.getenv("OCR_WORKERS", "2"))
    llm_concurrency: int = int(os.getenv("LLM_CONCURRENCY", "1"))
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_enabled: bool = os.getenv("NEO4J_ENABLED", "false").lower() == "true"
    require_neo4j: bool = os.getenv("REQUIRE_NEO4J", "false").lower() == "true"

    def validate(self) -> None:
        if self.host not in {"127.0.0.1", "localhost"}:
            raise ValueError("Development backend must bind only to localhost")
        if not is_approved_local_url(self.frontend_origin):
            raise ValueError("FRONTEND_ORIGIN must be local/private")
        if not is_approved_local_url(self.neo4j_uri):
            raise ValueError("NEO4J_URI must be local/private")
        ModelConfig.from_env()

    def ensure_directories(self) -> None:
        self.cases_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
