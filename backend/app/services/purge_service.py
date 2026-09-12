"""Destructive local cleanup for sensitive runtime data."""
from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import settings
from app.storage.sqlite import db


TABLES = ("translation_cache", "judgment_chunks", "judgments", "relations", "objects", "findings", "chunks", "pages", "documents", "jobs", "audits", "cases")


def _clear_directory(directory: Path, preserve: set[str] | None = None) -> int:
    preserve = preserve or set()
    removed = 0
    if not directory.exists():
        return removed
    for child in directory.iterdir():
        if child.name in preserve:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


def purge_all_data() -> dict:
    """Delete all user case/judgment data and compact the active database."""
    counts: dict[str, int] = {}
    with db.connect() as connection:
        for table in TABLES:
            counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            connection.execute(f"DELETE FROM {table}")

    with db.connect() as connection:
        connection.execute("VACUUM")
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    counts["case_directories"] = _clear_directory(settings.cases_dir, preserve={".gitkeep"})
    counts["judgment_files"] = _clear_directory(settings.data_dir / "legal_kb" / "judgments")

    # Remove the old alternate runtime database name if a previous build created it.
    legacy_db = settings.data_dir / "chargesheet.sqlite"
    if legacy_db.exists():
        legacy_db.unlink()
        counts["legacy_database"] = 1
    else:
        counts["legacy_database"] = 0
    return counts
