from __future__ import annotations

import json

from app.agents.contradiction_agent import contradiction_findings
from app.agents.missing_link_agent import missing_link_findings
from app.agents.quality_agent import quality_findings
from app.agents.strong_points_agent import strong_findings
from app.agents.verifier_agent import verify_findings
from app.agents.weak_points_agent import weak_findings
from app.storage.sqlite import db


def generate_findings(case_id: str, objects: list[dict], chunks: list[dict]) -> list[dict]:
    chunks_by_id = {chunk["id"]: chunk for chunk in chunks}
    findings = (strong_findings(objects, chunks_by_id) + weak_findings(objects, chunks_by_id) +
                contradiction_findings(chunks) + quality_findings(chunks) + missing_link_findings(objects, chunks_by_id))
    findings = verify_findings(findings, set(chunks_by_id))
    with db.connect() as con:
        con.execute("DELETE FROM findings WHERE case_id=?", (case_id,))
        for finding in findings:
            con.execute("INSERT INTO findings(id,case_id,type,data_json) VALUES(?,?,?,?)",
                        (finding["id"], case_id, finding["type"], json.dumps(finding, ensure_ascii=False)))
    return findings


def get_findings(case_id: str, finding_type: str | None = None) -> list[dict]:
    sql, params = "SELECT data_json FROM findings WHERE case_id=?", (case_id,)
    if finding_type:
        sql += " AND type=?"
        params += (finding_type,)
    return [json.loads(row["data_json"]) for row in db.all(sql, params)]

