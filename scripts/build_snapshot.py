"""Create a sanitized, portable Render snapshot bundle.

The default output is outside the repository. A caller must deliberately copy
an audited public-only bundle into ``demo_snapshot/`` if it should be included
in a deployment image.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if source.exists():
        for child in source.iterdir():
            destination = target / child.name
            if child.is_dir():
                shutil.copytree(child, destination)
            elif child.is_file():
                shutil.copy2(child, destination)


def _counts(database: Path) -> dict[str, int]:
    connection = sqlite3.connect(database)
    try:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in tables}
    finally:
        connection.close()


def build_snapshot(source_db: Path, source_cases: Path, source_legal_kb: Path, output: Path, replace: bool) -> None:
    source_db = source_db.resolve()
    output = output.resolve()
    protected = [REPO_ROOT.resolve(), source_db.parent, source_cases.resolve(), source_legal_kb.resolve(), Path.home().resolve()]
    if any(output == path or output in path.parents for path in protected):
        raise SystemExit("Output must not replace a source directory, repository, or home directory")
    if any(path in output.parents for path in [source_cases.resolve(), source_legal_kb.resolve(), source_db.parent]):
        raise SystemExit("Output must be outside runtime source directories")
    if not source_db.exists():
        raise SystemExit(f"Database not found: {source_db}")
    if output.exists() and any(output.iterdir()):
        if not replace:
            raise SystemExit(f"Output is not empty: {output}. Use --replace only after checking the target.")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    database_copy = output / "chargesheet.db"
    with sqlite3.connect(source_db) as source, sqlite3.connect(database_copy) as destination:
        source.backup(destination)
        destination.execute("DELETE FROM audits")
        # Stored absolute workstation paths are not portable deployment data.
        for judgment_id, in destination.execute("SELECT id FROM judgments").fetchall():
            destination.execute("UPDATE judgments SET stored_path=? WHERE id=?", (f"legal_kb/judgments/{judgment_id}.pdf", judgment_id))
        destination.commit()
        # Rebuild pages so previously deleted private records cannot remain in
        # SQLite free pages in the exported artifact.
        destination.execute("VACUUM")
    _copy_tree(source_cases.resolve(), output / "cases")
    _copy_tree(source_legal_kb.resolve(), output / "legal_kb")

    manifest = {
        "format": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "source_is_runtime_only": True,
        "counts": _counts(database_copy),
        "contents": ["chargesheet.db", "cases/", "legal_kb/"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshot created at: {output}")
    print(json.dumps(manifest["counts"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a portable read-only Render snapshot.")
    parser.add_argument("--output", type=Path, default=REPO_ROOT.parent / "chargesheet-render-snapshot",
                        help="Output directory; defaults outside the repository")
    parser.add_argument("--database", type=Path, default=REPO_ROOT / "data" / "chargesheet.db")
    parser.add_argument("--cases", type=Path, default=REPO_ROOT / "data" / "cases")
    parser.add_argument("--legal-kb", type=Path, default=REPO_ROOT / "data" / "legal_kb")
    parser.add_argument("--replace", action="store_true", help="Replace the exact output directory after checking it")
    args = parser.parse_args()
    build_snapshot(args.database, args.cases, args.legal_kb, args.output, args.replace)


if __name__ == "__main__":
    main()
