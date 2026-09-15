"""Seed a Render container from an offline-built, non-sensitive snapshot."""
from __future__ import annotations

import shutil
from pathlib import Path


def _replace_directory(source: Path, target: Path) -> None:
    if not source.exists():
        return
    if source.resolve() == target.resolve():
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def seed_snapshot(settings, database_path: Path) -> dict[str, int | bool]:
    """Copy the optional snapshot into the runtime data directory.

    The snapshot directory is deliberately outside normal ``data/`` runtime
    storage. A container starts with a clean writable filesystem, so copying
    the database and document files once at startup makes all read APIs work
    without shipping Ollama, OCR, or Neo4j. If no snapshot is present the
    service starts as an empty read-only demo, which is still useful for smoke
    testing the UI.
    """
    if not getattr(settings, "render_demo", False):
        return {"enabled": False, "seeded": False}

    source_root = Path(settings.snapshot_dir)
    source_db = source_root / "chargesheet.db"
    if not source_db.exists():
        return {"enabled": True, "seeded": False}

    database_path.parent.mkdir(parents=True, exist_ok=True)
    # Do not leave a stale SQLite journal/WAL alongside a replaced snapshot.
    for suffix in ("-wal", "-shm", "-journal"):
        database_path.with_name(database_path.name + suffix).unlink(missing_ok=True)
    if source_db.resolve() != database_path.resolve():
        shutil.copy2(source_db, database_path)

    _replace_directory(source_root / "cases", Path(settings.cases_dir))
    _replace_directory(source_root / "legal_kb", Path(settings.data_dir) / "legal_kb")
    return {"enabled": True, "seeded": True}
