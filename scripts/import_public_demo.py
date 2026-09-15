"""Build the public Render demo from an isolated staging workspace.

This command intentionally does not use the active ``data/`` directory. It
starts from the audited public snapshot, adds the verified public judgment
artifacts as separate incomplete source cases, warms reusable outputs locally,
and optionally exports a new ``demo_snapshot/`` bundle.

The source catalog is build-time input only. The hosted application never
fetches these URLs and never runs document processing or model inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE = REPO_ROOT.parent / "chargesheet-public-demo-stage"
CATALOG_PATH = REPO_ROOT / "scripts" / "public_demo_sources.json"
MAX_ARTIFACT_BYTES = 250 * 1024 * 1024


class SourceRejected(ValueError):
    """A public catalog entry is not safe or usable for the snapshot."""


def _load_catalog() -> list[dict]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SourceRejected("The public source catalog contains no sources")
    return sources


def _safe_stage_path(value: Path) -> Path:
    path = value.expanduser().resolve()
    # The importer is deliberately constrained to a sibling staging directory.
    # This makes --replace unable to target the repository, runtime data, or a
    # broad user directory by accident.
    if path.parent != REPO_ROOT.parent.resolve() or path == REPO_ROOT.resolve():
        raise SourceRejected(f"Stage directory must be a direct sibling of the repository: {path}")
    if not path.name.startswith("chargesheet-"):
        raise SourceRejected("Stage directory must use a chargesheet-* name")
    return path


def _safe_artifact_path(relative: str) -> Path:
    path = (REPO_ROOT / relative).resolve()
    allowed_root = (REPO_ROOT / "demo_snapshot").resolve()
    if allowed_root not in path.parents or not path.is_file():
        raise SourceRejected(f"Public artifact is missing or outside demo_snapshot: {relative}")
    return path


def _copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise SourceRejected(f"Public snapshot source is missing: {source}")
    shutil.copytree(source, target)


def _validate_pdf(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    if len(data) > MAX_ARTIFACT_BYTES:
        raise SourceRejected(f"Artifact is larger than {MAX_ARTIFACT_BYTES // (1024 * 1024)} MB: {path.name}")
    if not data.startswith(b"%PDF-"):
        raise SourceRejected(f"Artifact is not a PDF; refusing to import it: {path.name}")
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.ingestion.pdf_loader import inspect_pdf

    try:
        page_count = inspect_pdf(path)["page_count"]
    except Exception as exc:
        raise SourceRejected(f"PDF validation failed for {path.name}: {exc}") from exc
    return hashlib.sha256(data).hexdigest(), int(page_count)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")[:70]


def _configure_staging(stage: Path) -> None:
    data_dir = stage / "data"
    os.environ.update({
        "DATA_DIR": str(data_dir),
        "DATABASE_PATH": str(data_dir / "chargesheet.db"),
        "CASES_DIR": str(data_dir / "cases"),
        "APP_ENV": "development",
        "DEMO_SNAPSHOT_MODE": "false",
        "FRONTEND_ORIGIN": "http://127.0.0.1:5173",
    })


def _prepare_stage(stage: Path, replace: bool) -> None:
    if stage.exists():
        if not replace:
            raise SourceRejected(f"Stage directory is not empty: {stage}. Use --replace after reviewing it.")
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    snapshot = REPO_ROOT / "demo_snapshot"
    data_dir = stage / "data"
    data_dir.mkdir()
    shutil.copy2(snapshot / "chargesheet.db", data_dir / "chargesheet.db")
    _copy_tree(snapshot / "cases", data_dir / "cases")
    _copy_tree(snapshot / "legal_kb", data_dir / "legal_kb")


def _assert_catalog(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    usable: list[dict] = []
    unavailable: list[dict] = []
    seen_ids: set[str] = set()
    seen_artifacts: set[str] = set()
    seen_hashes: set[str] = set()
    for source in sources:
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id or source_id in seen_ids:
            raise SourceRejected(f"Catalog contains an invalid or duplicate source id: {source_id!r}")
        seen_ids.add(source_id)
        status = source.get("status")
        artifact = source.get("artifact")
        if status == "verified_pdf":
            if not isinstance(artifact, str) or not artifact:
                raise SourceRejected(f"Verified source has no local artifact: {source_id}")
            if artifact in seen_artifacts:
                raise SourceRejected(f"Catalog reuses a verified artifact: {artifact}")
            seen_artifacts.add(artifact)
            digest, pages = _validate_pdf(_safe_artifact_path(artifact))
            expected_digest = source.get("sha256")
            if expected_digest and expected_digest != digest:
                raise SourceRejected(f"Catalog hash does not match artifact for {source_id}")
            expected_pages = source.get("page_count")
            if expected_pages is not None:
                try:
                    expected_pages = int(expected_pages)
                except (TypeError, ValueError) as exc:
                    raise SourceRejected(f"Catalog page count is invalid for {source_id}") from exc
                if expected_pages != pages:
                    raise SourceRejected(f"Catalog page count does not match artifact for {source_id}")
            if digest in seen_hashes:
                raise SourceRejected(f"Catalog contains duplicate PDF content: {source_id}")
            seen_hashes.add(digest)
            usable.append({**source, "sha256": digest, "page_count": pages})
        elif status == "unavailable_404":
            if artifact:
                raise SourceRejected(f"Unavailable source unexpectedly has an artifact: {source_id}")
            if not isinstance(source.get("url"), str) or not source["url"].startswith(("http://", "https://")):
                raise SourceRejected(f"Unavailable source has no valid attribution URL: {source_id}")
            unavailable.append(source)
        else:
            raise SourceRejected(f"Unsupported source status for {source_id}: {status!r}")
    return usable, unavailable


def _import_cases(stage: Path, usable: list[dict]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.services.case_service import create_case, save_document
    from app.services.processing_service import process_case
    from app.storage.sqlite import db

    db.initialize()
    sample = next((item for item in usable if item["source_type"] == "educational_sample"), None)
    if sample:
        sample_case_id = sample.get("case_id")
        if sample_case_id:
            db.execute("UPDATE cases SET record_type='educational_sample' WHERE id=?", (sample_case_id,))
            db.execute("UPDATE documents SET source_url=? WHERE case_id=?", (sample["url"], sample_case_id))

    for source in usable:
        if source["source_type"] != "public_judgment":
            continue
        source_id = source["id"]
        case_id = f"case_public_{_slug(source_id)}"
        document_id = f"doc_public_{_slug(source_id)}"
        artifact = _safe_artifact_path(source["artifact"])
        data = artifact.read_bytes()
        existing = db.one("SELECT id,record_type FROM cases WHERE id=?", (case_id,))
        if existing:
            if existing.get("record_type") != "public_judgment":
                raise SourceRejected(f"Deterministic case id is already used by another record: {case_id}")
            document = db.one("SELECT sha256 FROM documents WHERE id=?", (document_id,))
            if not document:
                raise SourceRejected(f"Existing public case has no expected document: {case_id}")
            if document["sha256"] != source["sha256"]:
                raise SourceRejected(f"Public artifact changed for existing case: {source_id}")
            job = db.one("SELECT state FROM jobs WHERE case_id=?", (case_id,))
            if job and job["state"] == "complete":
                print(f"Reused processed public case: {source['title']}")
                continue
        else:
            create_case({
                "case_number": f"PUBLIC-JUDGMENT-{_slug(source_id).upper()}",
                "police_station": "Not applicable — public court record",
                "language": "English",
                "record_type": "public_judgment",
            }, case_id=case_id)
            save_document(
                case_id,
                artifact.name,
                data,
                role="supporting_record",
                source_url=source["url"],
                document_id=document_id,
            )
        process_case(case_id)
        job = db.one("SELECT state,error FROM jobs WHERE case_id=?", (case_id,))
        if not job or job["state"] != "complete":
            raise RuntimeError(f"Processing failed for {source_id}: {job.get('error') if job else 'no job'}")
        print(f"Processed public case: {source['title']} ({source['page_count']} source pages)")


def _warm_and_export(stage: Path, export: bool, replace: bool, usable: list[dict], unavailable: list[dict]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from precompute_snapshot import main as precompute_main

    precompute_main()
    if not export:
        return
    from build_snapshot import build_snapshot

    output = REPO_ROOT / "demo_snapshot"
    if output.exists() and any(output.iterdir()) and not replace:
        raise SourceRejected(f"Snapshot is not empty: {output}. Use --replace to export it.")
    build_snapshot(
        source_db=stage / "data" / "chargesheet.db",
        source_cases=stage / "data" / "cases",
        source_legal_kb=stage / "data" / "legal_kb",
        output=output,
        replace=replace,
    )
    report = {
        "catalog_version": 1,
        "usable_sources": [
            {"id": item["id"], "title": item["title"], "status": item["status"],
             "source_type": item["source_type"], "url": item["url"],
             "sha256": item["sha256"], "page_count": item["page_count"]}
            for item in usable
        ],
        "unavailable_sources": [
            {"id": item["id"], "title": item["title"], "status": item["status"], "url": item["url"]}
            for item in unavailable
        ],
    }
    report_path = output / "public_source_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # build_snapshot writes its manifest before this report exists. Keep the
    # manifest truthful so an auditor can enumerate the complete bundle.
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contents = list(manifest.get("contents", []))
    if report_path.name not in contents:
        contents.append(report_path.name)
    manifest["contents"] = contents
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported public Render snapshot with {len(usable)} usable and {len(unavailable)} unavailable catalog entries")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the isolated public Render demo dataset.")
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE,
                        help="Sibling staging directory; never the active data directory")
    parser.add_argument("--replace", action="store_true",
                        help="Replace the exact sibling stage and deployment snapshot after validation")
    parser.add_argument("--reuse-stage", action="store_true",
                        help="Reuse an already validated sibling stage instead of copying demo_snapshot again")
    parser.add_argument("--no-export", action="store_true",
                        help="Process and warm staging data without replacing demo_snapshot")
    args = parser.parse_args()

    stage = _safe_stage_path(args.stage_dir)
    sources = _load_catalog()
    usable, unavailable = _assert_catalog(sources)
    if args.reuse_stage:
        if not (stage / "data" / "chargesheet.db").is_file():
            raise SourceRejected(f"Reusable staging database is missing: {stage}")
    else:
        _prepare_stage(stage, args.replace)
    _configure_staging(stage)
    _import_cases(stage, usable)
    _warm_and_export(stage, export=not args.no_export, replace=args.replace,
                     usable=usable, unavailable=unavailable)
    print(f"Staging workspace: {stage}")


if __name__ == "__main__":
    main()
