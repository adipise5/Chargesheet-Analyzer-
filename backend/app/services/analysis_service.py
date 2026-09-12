from __future__ import annotations

import json

from app.agents.contradiction_agent import contradiction_findings
from app.agents.missing_link_agent import missing_link_findings
from app.agents.quality_agent import quality_findings
from app.agents.strong_points_agent import strong_findings
from app.agents.verifier_agent import verify_findings
from app.agents.weak_points_agent import weak_findings
from app.analysis.comparative import comparative_findings, completeness_findings, custody_findings
from app.analysis.format_checks import draft_quality_findings
from app.storage.sqlite import db


def generate_findings(case_id: str, objects: list[dict], chunks: list[dict]) -> list[dict]:
    chunks_by_id = {chunk["id"]: chunk for chunk in chunks}
    documents = db.all("SELECT * FROM documents WHERE case_id=?", (case_id,))
    findings = (strong_findings(objects, chunks_by_id) + weak_findings(objects, chunks_by_id) +
                contradiction_findings(chunks) + quality_findings(chunks) + missing_link_findings(objects, chunks_by_id))
    findings += comparative_findings(documents, chunks) + completeness_findings(documents, chunks) + custody_findings(documents, chunks) + draft_quality_findings(documents, chunks)
    for finding in findings:
        _add_action_fields(finding)
    findings = verify_findings(findings, set(chunks_by_id))
    with db.connect() as con:
        con.execute("DELETE FROM findings WHERE case_id=?", (case_id,))
        for finding in findings:
            con.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
                        (finding["id"], case_id, finding["type"], json.dumps(finding, ensure_ascii=False)))
    return findings


def _add_action_fields(finding: dict) -> None:
    """Give every machine finding an explicit issue/impact/action explanation."""
    finding.setdefault("issue", finding.get("summary", ""))
    finding.setdefault("differences", [])
    finding.setdefault("why_important", "This item may affect the reliability or completeness of the filing and requires human verification.")
    finding.setdefault("recommended_correction", "Verify the cited source pages and correct the draft record or document the explanation.")
    finding.setdefault("io_action", "Review the cited pages, verify against the original record, and record the outcome before filing.")
    finding.setdefault("defense_questions", ["What is the source for this assertion?", "Can the IO explain this issue with the original record?"])
    finding.setdefault("related_document_roles", [])
    if finding["type"] == "weak_point":
        if finding.get("summary", "").startswith("This candidate claim is presently linked to a single source passage"):
            page = (finding.get("supporting_sources") or [{}])[0].get("page", "the cited")
            claim = finding.get("title", "This extracted claim")[:180]
            finding["summary"] = f"This extracted claim — {claim} — is linked to only one source passage (page {page}). No second document or independent supporting link was located in the uploaded record."
            finding["why_important"] = "A single-source claim may be challenged as uncorroborated if no independent record supports it."
            finding["recommended_correction"] = "Check the FIR, witness statements, medical/forensic records, seizure memo, and digital material for independent support; qualify the claim if none exists."
            finding["io_action"] = f"Review the source passage on page {page} and record which independent document or witness, if any, corroborates this claim."
            finding["defense_questions"] = ["What independent evidence corroborates this claim?", f"Why is this claim presently supported only by page {page}?"]
    elif finding["type"] == "contradiction":
        finding["why_important"] = "An unresolved contradiction can undermine witness credibility and the sequence of events."
        finding["recommended_correction"] = "Resolve the conflict from the original record or clearly preserve and explain the uncertainty."
        finding["io_action"] = "Interview the relevant witness or inspect the primary record and document the resolution."
    elif finding["type"] == "potential_mistake":
        finding["why_important"] = "An incorrect identifier can connect the allegation to the wrong person, vehicle, item, or record."
        finding["recommended_correction"] = "Verify the identifier against the primary record and correct every affected reference."


def get_findings(case_id: str, finding_type: str | None = None) -> list[dict]:
    sql, params = "SELECT data_json FROM findings WHERE case_id=?", (case_id,)
    if finding_type:
        sql += " AND type=?"
        params += (finding_type,)
    findings = [json.loads(row["data_json"]) for row in db.all(sql, params)]
    for finding in findings:
        _add_action_fields(finding)
    return findings

