from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.security import safe_display_filename, validate_pdf_bytes
from app.extraction.entity_resolution import normalize_text
from app.ingestion.pdf_loader import inspect_pdf
from app.services.ollama_service import OllamaService
from app.storage.sqlite import db, now_iso


def _root() -> Path:
    path = settings.data_dir / "legal_kb" / "judgments"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_judgment(filename: str | None, data: bytes, title: str = "", court: str = "", year: str = "") -> dict:
    validate_pdf_bytes(data, filename, settings.max_upload_bytes)
    judgment_id = f"judgment_{uuid.uuid4().hex}"
    safe_name = safe_display_filename(filename)
    path = _root() / f"{judgment_id}.pdf"
    path.write_bytes(data)
    try:
        page_count = inspect_pdf(path)["page_count"]
        import fitz
        document = fitz.open(path)
        with db.connect() as con:
            con.execute("INSERT INTO judgments(id,title,court,judgment_year,filename,stored_path,page_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
                        (judgment_id, title.strip() or safe_name, court.strip(), year.strip(), safe_name, str(path), page_count, now_iso()))
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if text:
                    con.execute("INSERT INTO judgment_chunks(id,judgment_id,page_number,text,normalized_text) VALUES(?,?,?,?,?)",
                                (f"jchunk_{uuid.uuid4().hex}", judgment_id, page_number, text, normalize_text(text).casefold()))
        document.close()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return db.one("SELECT id,title,court,judgment_year,filename,page_count,created_at FROM judgments WHERE id=?", (judgment_id,))


def list_judgments() -> list[dict]:
    return db.all("SELECT id,title,court,judgment_year,filename,page_count,created_at FROM judgments ORDER BY created_at DESC")


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[\w\u0A80-\u0AFF]{4,}", value.casefold())}


def _precedent_fingerprint(case_id: str, findings: list[dict], judgment_rows: list[dict]) -> str:
    """Fingerprint the case review and local judgment corpus used for matching."""
    stable_findings = []
    for row in findings:
        try:
            finding = json.loads(row["data_json"])
            finding.pop("id", None)  # IDs are regenerated on every rebuild.
            stable_findings.append(finding)
        except (TypeError, json.JSONDecodeError):
            stable_findings.append(row["data_json"])
    payload = {
        "case_id": case_id,
        "findings": stable_findings,
        "judgments": [
            {key: row.get(key) for key in ("id", "judgment_id", "page_number", "text", "title", "court", "judgment_year")}
            for row in judgment_rows
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def analyze_precedents(case_id: str) -> dict:
    findings = db.all("SELECT data_json FROM findings WHERE case_id=?", (case_id,))
    case_text = " ".join(row["data_json"] for row in findings)
    query_terms = _tokens(case_text) | {"contradiction", "witness", "evidence", "investigation", "custody"}
    rows = db.all("SELECT c.*,j.title,j.court,j.judgment_year FROM judgment_chunks c JOIN judgments j ON j.id=c.judgment_id")
    fingerprint = _precedent_fingerprint(case_id, findings, rows)
    cached = db.one("SELECT precedents_json FROM cases WHERE id=? AND precedents_fingerprint=?", (case_id, fingerprint))
    if cached and cached.get("precedents_json"):
        try:
            candidate = json.loads(cached["precedents_json"])
            if isinstance(candidate, dict) and isinstance(candidate.get("insights"), str) and isinstance(candidate.get("citations"), list):
                return candidate
        except (TypeError, json.JSONDecodeError):
            pass
    scored = []
    for row in rows:
        overlap = len(query_terms & _tokens(row["text"]))
        if overlap:
            scored.append((overlap, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [row for _, row in scored[:8]]
    citations = [{"judgment_id": row["judgment_id"], "page": row["page_number"], "chunk_id": row["id"],
                  "label": f"{row['title']} — p{row['page_number']}"} for row in selected]
    if not selected:
        result = {"insights": "No relevant local judgments were found. Import approved local judgments before using precedent analysis.", "citations": [], "review_required": True, "matches": []}
        db.execute("UPDATE cases SET precedents_json=?,precedents_fingerprint=? WHERE id=?", (json.dumps(result, ensure_ascii=False), fingerprint, case_id))
        return result
    context = "\n\n".join(f"SOURCE {index + 1} ({row['title']}, page {row['page_number']}):\n{row['text'][:4500]}" for index, row in enumerate(selected))
    prompt = ("You are a local legal-research assistant. Based only on the supplied judgment excerpts, identify recurring prosecution weaknesses or court concerns relevant to this case. "
              "Do not state that a court will reach a particular result, do not invent holdings, and distinguish quotation from inference. Give practical verification points for the investigating officer. Cite SOURCE numbers.\n\n" + context)
    try:
        insights = OllamaService().answer(prompt)
        review_required = False
    except Exception:
        excerpts = [" ".join(row["text"].split())[:400] for row in selected[:5]]
        insights = "Relevant local judgment passages were found. Review them for recurring concerns before drawing any legal conclusion:\n" + "\n".join(
            f"• {excerpt} ({row['title']}, p.{row['page_number']})" for excerpt, row in zip(excerpts, selected[:5]))
        review_required = True
    result = {"insights": insights, "citations": citations, "review_required": review_required,
              "matches": [{"title": row["title"], "court": row["court"], "year": row["judgment_year"], "page": row["page_number"], "score": score}
                          for score, row in scored[:8]]}
    db.execute("UPDATE cases SET precedents_json=?,precedents_fingerprint=? WHERE id=?", (json.dumps(result, ensure_ascii=False), fingerprint, case_id))
    return result
