"""Warm reusable outputs before exporting a Render demo snapshot.

Run this from the repository's normal local environment, after processing the
public demo records and importing the approved judgment corpus. Interactive
Ask Case messages remain ephemeral; only the four intentionally supported demo
questions below are persisted for the model-free hosted path. The same pass
  also prepares both English and Gujarati translations for the dynamic text
  rendered by the snapshot, so changing language on Render does not invoke a
  model.
"""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import settings  # noqa: E402
from app.api.system import TranslationRequest, translate  # noqa: E402
from app.agents.summary_agent import _fallback as fallback_summary  # noqa: E402
from app.graph.repository import graph_repository  # noqa: E402
from app.services.analysis_service import get_findings  # noqa: E402
from app.services.judgment_service import analyze_precedents  # noqa: E402
from app.services.query_service import query_case  # noqa: E402
from app.storage.sqlite import db  # noqa: E402


DEMO_QUESTIONS = (
    "What is this case about?",
    "What should I verify before filing this charge sheet?",
    "Which claims rely on a single source?",
    "Which evidence items are not linked to any claim?",
)


def _add(values: list[str], value: object) -> None:
    if isinstance(value, str) and value.strip() and len(value.strip()) <= 2400:
        values.append(value.strip())


def _translation_inputs(case_id: str, answers: list[dict], precedent: dict) -> list[str]:
    values: list[str] = []
    case = db.one("SELECT summary_json FROM cases WHERE id=?", (case_id,)) or {}
    try:
        summary = json.loads(case.get("summary_json") or "{}")
    except (TypeError, json.JSONDecodeError):
        summary = {}
    _add(values, summary.get("english"))
    _add(values, precedent.get("insights"))
    for answer in answers:
        _add(values, answer.get("answer"))
    for finding in get_findings(case_id):
        for key in ("title", "summary", "issue", "why_important", "recommended_correction", "io_action"):
            _add(values, finding.get(key))
        for question in finding.get("defense_questions", []):
            _add(values, question)
        for difference in finding.get("differences", []):
            _add(values, difference.get("role"))
            _add(values, difference.get("value"))
    graph = graph_repository.data(case_id)
    for node in graph.get("nodes", []):
        _add(values, node.get("label"))
        for alias in node.get("aliases", []):
            _add(values, alias)
    return list(dict.fromkeys(values))


def _has_gujarati(value: str) -> bool:
    return any("\u0A80" <= char <= "\u0AFF" for char in value)


def _warm_language(values: list[str], target: str) -> dict[str, str]:
    translated: dict[str, str] = {}

    def collect(source_values: list[str], outputs: object) -> None:
        if not isinstance(outputs, list):
            return
        for source, translated_text in zip(source_values, outputs):
            if isinstance(translated_text, str) and translated_text.strip() and (target == "english" or _has_gujarati(translated_text)):
                translated[source] = translated_text.strip()

    for start in range(0, len(values), 3):
        batch = values[start:start + 3]
        try:
            response = translate(TranslationRequest(texts=batch, target=target))
        except Exception as exc:  # pragma: no cover - depends on local model availability
            print(f"Warning: {target} translation batch failed: {exc}")
            continue
        collect(batch, response.get("translations", []))
        if response.get("fallback") and len(batch) > 1:
            # The compact local model can fail to keep a multi-item JSON
            # response aligned. Retry only the items that were not accepted so
            # the exported snapshot has complete language coverage.
            for source in batch:
                if source in translated:
                    continue
                try:
                    retry = translate(TranslationRequest(texts=[source], target=target))
                except Exception as exc:  # pragma: no cover - depends on local model availability
                    print(f"Warning: {target} translation retry failed: {exc}")
                    continue
                collect([source], retry.get("translations", []))
        if response.get("fallback"):
            print(f"Warning: {target} translation fallback for batch starting at item {start + 1}")
    return translated


def _save_summary_translation(case_id: str, translated: dict[str, str]) -> None:
    row = db.one("SELECT summary_json FROM cases WHERE id=?", (case_id,))
    if not row or not row.get("summary_json"):
        return
    try:
        summary = json.loads(row["summary_json"])
    except (TypeError, json.JSONDecodeError):
        return
    english = summary.get("english")
    gujarati = translated.get(english) if isinstance(english, str) else None
    if isinstance(english, str) and not gujarati:
        digest = hashlib.sha256(english.encode("utf-8")).hexdigest()
        cached = db.one("SELECT translated_text FROM translation_cache WHERE text_hash=? AND target='gujarati'", (digest,))
        gujarati = cached.get("translated_text") if cached else None
    if not (gujarati and _has_gujarati(gujarati)):
        # A compact local model can occasionally return malformed output for a
        # single long item. Keep the hosted Overview fully bilingual without
        # doing inference at runtime by using the same conservative, factual
        # fallback used by the live summary agent.
        case = db.one("SELECT * FROM cases WHERE id=?", (case_id,)) or {"case_number": case_id}
        object_counts = {row["kind"]: row["count"] for row in db.all(
            "SELECT kind,COUNT(*) count FROM objects WHERE case_id=? GROUP BY kind", (case_id,))}
        counts = {
            "documents": db.one("SELECT COUNT(*) count FROM documents WHERE case_id=?", (case_id,))["count"],
            "pages": db.one("SELECT COUNT(*) count FROM pages WHERE case_id=?", (case_id,))["count"],
            "claims": object_counts.get("Claim", 0),
            "evidence": sum(object_counts.get(kind, 0) for kind in ("Evidence", "DigitalEvidence", "PhysicalEvidence", "ForensicEvidence")),
        }
        gujarati = fallback_summary(case, counts)["gujarati"]
    summary["gujarati"] = gujarati
    db.execute("UPDATE cases SET summary_json=? WHERE id=?", (json.dumps(summary, ensure_ascii=False), case_id))


def main() -> None:
    if settings.render_demo:
        raise SystemExit("Run precompute_snapshot.py in local mode, before enabling APP_ENV=render_demo.")
    db.initialize()
    cases = db.all("SELECT id,case_number,status FROM cases ORDER BY id")
    if not cases:
        raise SystemExit("No cases are present. Process public demo records before exporting a snapshot.")
    for case in cases:
        if db.one("SELECT 1 FROM judgment_chunks LIMIT 1"):
            precedent = analyze_precedents(case["id"])
        else:
            precedent = {}
        answers = []
        for question in DEMO_QUESTIONS:
            answers.append(query_case(case["id"], question, persist=True))
        translation_inputs = _translation_inputs(case["id"], answers, precedent)
        gujarati = _warm_language(translation_inputs, "gujarati")
        english = _warm_language(translation_inputs, "english")
        _save_summary_translation(case["id"], gujarati)
        print(f"Warmed reusable outputs for {case['case_number']} ({case['status']}); prepared {len(english)}/{len(translation_inputs)} English and {len(gujarati)}/{len(translation_inputs)} Gujarati strings")
    print(f"Prepared {len(cases)} case(s); interactive chat is not persisted.")


if __name__ == "__main__":
    main()
