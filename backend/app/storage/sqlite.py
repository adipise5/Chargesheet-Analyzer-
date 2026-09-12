from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from app.core.config import settings


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY, case_number TEXT NOT NULL, police_station TEXT NOT NULL,
  language TEXT NOT NULL, status TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  summary_json TEXT, summary_fingerprint TEXT
);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  filename TEXT NOT NULL, stored_name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'unknown',
  page_count INTEGER NOT NULL DEFAULT 0, sha256 TEXT NOT NULL, status TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'supporting_record', created_at TEXT NOT NULL, UNIQUE(case_id, sha256)
);
CREATE TABLE IF NOT EXISTS pages (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL, extraction_method TEXT NOT NULL, language TEXT NOT NULL,
  original_text TEXT NOT NULL, normalized_text TEXT NOT NULL, ocr_confidence REAL NOT NULL,
  review_status TEXT NOT NULL, tesseract_text TEXT, vision_candidate_text TEXT, corrected_text TEXT,
  image_path TEXT, blocks_json TEXT NOT NULL DEFAULT '[]', updated_at TEXT NOT NULL,
  UNIQUE(document_id, page_number)
);
CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL, document_id TEXT NOT NULL, page_number INTEGER NOT NULL,
  text TEXT NOT NULL, normalized_text TEXT NOT NULL, language TEXT NOT NULL,
  embedding_json TEXT, metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS objects (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL, kind TEXT NOT NULL, subtype TEXT NOT NULL,
  label TEXT NOT NULL, data_json TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 1.0
);
CREATE TABLE IF NOT EXISTS relations (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL, source_id TEXT NOT NULL, target_id TEXT NOT NULL,
  relation TEXT NOT NULL, confidence REAL NOT NULL, citations_json TEXT NOT NULL,
  extraction_method TEXT NOT NULL, human_verified INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS findings (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL, type TEXT NOT NULL, data_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY, case_id TEXT NOT NULL UNIQUE, state TEXT NOT NULL, stage TEXT NOT NULL,
  progress INTEGER NOT NULL, counts_json TEXT NOT NULL, stages_json TEXT NOT NULL,
  error TEXT, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audits (
  id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, event TEXT NOT NULL,
  metadata_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS judgments (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, court TEXT NOT NULL DEFAULT '', judgment_year TEXT NOT NULL DEFAULT '',
  filename TEXT NOT NULL, stored_path TEXT NOT NULL, page_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS judgment_chunks (
  id TEXT PRIMARY KEY, judgment_id TEXT NOT NULL REFERENCES judgments(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL, text TEXT NOT NULL, normalized_text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_case ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_pages_case ON pages(case_id);
CREATE INDEX IF NOT EXISTS idx_chunks_case ON chunks(case_id);
CREATE INDEX IF NOT EXISTS idx_objects_case ON objects(case_id);
CREATE INDEX IF NOT EXISTS idx_relations_case ON relations(case_id);
CREATE INDEX IF NOT EXISTS idx_findings_case ON findings(case_id);
CREATE INDEX IF NOT EXISTS idx_judgment_chunks_judgment ON judgment_chunks(judgment_id);
"""


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path | None = None):
        self.path = path or settings.database_path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(documents)").fetchall()}
            if "role" not in columns:
                connection.execute("ALTER TABLE documents ADD COLUMN role TEXT NOT NULL DEFAULT 'supporting_record'")
            case_columns = {row[1] for row in connection.execute("PRAGMA table_info(cases)").fetchall()}
            if "summary_json" not in case_columns:
                connection.execute("ALTER TABLE cases ADD COLUMN summary_json TEXT")
            if "summary_fingerprint" not in case_columns:
                connection.execute("ALTER TABLE cases ADD COLUMN summary_fingerprint TEXT")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(sql, params).fetchone()
        return dict(row) if row else None

    def all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.connect() as connection:
            connection.execute(sql, params)

    def audit(self, event: str, case_id: str | None = None, metadata: dict | None = None) -> None:
        # Metadata must remain operational only. Never store source text or model I/O here.
        safe = {k: v for k, v in (metadata or {}).items() if k in {"document_id", "page", "count", "stage", "method"}}
        self.execute(
            "INSERT INTO audits(case_id,event,metadata_json,created_at) VALUES(?,?,?,?)",
            (case_id, event, json.dumps(safe), now_iso()),
        )


db = Database()

