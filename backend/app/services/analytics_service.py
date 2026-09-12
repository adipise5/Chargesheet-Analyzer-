"""Cross-case analytics aggregation service.

Runs read-only aggregate SQL queries against the existing SQLite database
to surface crime patterns, seasonality, hotspots, and other macro-level insights.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

from app.storage.sqlite import db


GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")


def _ascii_digits(value: str) -> str:
    """Normalize Gujarati numerals for aggregation without changing source text."""
    return value.translate(GUJARATI_DIGITS)


def global_summary() -> dict:
    """Top-level statistics across all cases."""
    cases_count = db.one("SELECT COUNT(*) count FROM cases WHERE is_demo=0", ())["count"]
    docs_count = db.one("SELECT COUNT(*) count FROM documents d JOIN cases c ON d.case_id=c.id WHERE c.is_demo=0", ())["count"]
    pages_count = db.one("SELECT COUNT(*) count FROM pages p JOIN cases c ON p.case_id=c.id WHERE c.is_demo=0", ())["count"]

    object_counts = db.all(
        "SELECT o.kind, COUNT(*) count FROM objects o JOIN cases c ON o.case_id=c.id WHERE c.is_demo=0 GROUP BY o.kind", ()
    )
    kind_map = {row["kind"]: row["count"] for row in object_counts}

    findings_count = db.one("SELECT COUNT(*) count FROM findings f JOIN cases c ON f.case_id=c.id WHERE c.is_demo=0", ())["count"]

    return {
        "total_cases": cases_count,
        "total_documents": docs_count,
        "total_pages": pages_count,
        "total_accused": kind_map.get("Accused", 0),
        "total_witnesses": kind_map.get("Witness", 0),
        "total_evidence": sum(kind_map.get(k, 0) for k in ("Evidence", "DigitalEvidence", "PhysicalEvidence", "ForensicEvidence")),
        "total_claims": kind_map.get("Claim", 0),
        "total_vehicles": kind_map.get("Vehicle", 0),
        "total_legal_sections": kind_map.get("LegalSection", 0),
        "total_findings": findings_count,
    }


def crime_type_distribution() -> list[dict]:
    """IPC/BNS section frequency across all non-demo cases."""
    rows = db.all(
        "SELECT o.label, COUNT(*) count FROM objects o JOIN cases c ON o.case_id=c.id "
        "WHERE c.is_demo=0 AND o.kind='LegalSection' GROUP BY o.label ORDER BY count DESC", ()
    )
    return [{"section": row["label"], "count": row["count"]} for row in rows]


def temporal_distribution() -> list[dict]:
    """Separate case registration, extraction completion, and source events by month."""
    rows = db.all("SELECT created_at FROM cases WHERE is_demo=0", ())
    registered_monthly: Counter = Counter()
    for row in rows:
        match = re.match(r"(\d{4})-(\d{2})", row["created_at"] or "")
        if match:
            registered_monthly[f"{match.group(1)}-{match.group(2)}"] += 1

    # Extraction completion is recorded by the processing job. Fall back to the
    # upload timestamp for legacy records that predate the jobs table.
    extracted_rows = db.all(
        "SELECT c.id, COALESCE(j.updated_at, MIN(d.created_at)) AS extracted_at "
        "FROM cases c LEFT JOIN jobs j ON j.case_id=c.id AND j.state='complete' "
        "LEFT JOIN documents d ON d.case_id=c.id WHERE c.is_demo=0 GROUP BY c.id", ()
    )
    extracted_monthly: Counter = Counter()
    for row in extracted_rows:
        match = re.match(r"(\d{4})-(\d{2})", row["extracted_at"] or "")
        if match:
            extracted_monthly[f"{match.group(1)}-{match.group(2)}"] += 1

    # Also include event dates from objects
    event_rows = db.all(
        "SELECT o.data_json FROM objects o JOIN cases c ON o.case_id=c.id "
        "WHERE c.is_demo=0 AND o.kind='Event'", ()
    )
    event_monthly: Counter = Counter()
    for row in event_rows:
        try:
            data = json.loads(row["data_json"])
            date = _ascii_digits(str(data.get("date", "")))
            # Try DD/MM/YYYY or DD-MM-YYYY format
            m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", date)
            if m:
                day, month, year = m.groups()
                if len(year) == 2:
                    year = f"20{year}" if int(year) < 50 else f"19{year}"
                key = f"{year}-{month.zfill(2)}"
                event_monthly[key] += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    # Merge both: case registration dates and event dates
    all_months = sorted(set(registered_monthly.keys()) | set(extracted_monthly.keys()) | set(event_monthly.keys()))
    return [{
        "month": m,
        "cases_registered": registered_monthly.get(m, 0),
        "cases_extracted": extracted_monthly.get(m, 0),
        "crime_events": event_monthly.get(m, 0),
    } for m in all_months]


def crime_hotspots() -> list[dict]:
    """Crime frequency by police station."""
    rows = db.all(
        "SELECT police_station, COUNT(*) count FROM cases WHERE is_demo=0 GROUP BY police_station ORDER BY count DESC", ()
    )
    return [{"station": row["police_station"], "count": row["count"]} for row in rows]


def case_status_distribution() -> list[dict]:
    """Case resolution pipeline status breakdown."""
    rows = db.all(
        "SELECT status, COUNT(*) count FROM cases WHERE is_demo=0 GROUP BY status ORDER BY count DESC", ()
    )
    return [{"status": row["status"], "count": row["count"]} for row in rows]


def evidence_profile() -> list[dict]:
    """Evidence type distribution across all cases."""
    rows = db.all(
        "SELECT o.subtype, COUNT(*) count FROM objects o JOIN cases c ON o.case_id=c.id "
        "WHERE c.is_demo=0 AND o.kind IN ('Evidence','DigitalEvidence','PhysicalEvidence','ForensicEvidence') "
        "GROUP BY o.subtype ORDER BY count DESC", ()
    )
    return [{"type": row["subtype"], "count": row["count"]} for row in rows]


def entity_network() -> list[dict]:
    """Top entities that appear across multiple cases (repeat offenders, common vehicles, etc.)."""
    rows = db.all(
        "SELECT o.label, o.kind, COUNT(DISTINCT o.case_id) case_count "
        "FROM objects o JOIN cases c ON o.case_id=c.id "
        "WHERE c.is_demo=0 AND o.kind IN ('Accused','Witness','Vehicle','Device') "
        "GROUP BY o.label, o.kind HAVING case_count > 1 ORDER BY case_count DESC LIMIT 30", ()
    )
    return [{"label": row["label"], "kind": row["kind"], "case_count": row["case_count"]} for row in rows]


def findings_summary() -> list[dict]:
    """Finding type distribution across all cases."""
    rows = db.all(
        "SELECT f.type, COUNT(*) count FROM findings f JOIN cases c ON f.case_id=c.id "
        "WHERE c.is_demo=0 GROUP BY f.type ORDER BY count DESC", ()
    )
    return [{"type": row["type"], "count": row["count"]} for row in rows]


def document_roles() -> list[dict]:
    """Distribution of document roles (FIR, chargesheet, etc.)."""
    rows = db.all(
        "SELECT d.role, COUNT(*) count FROM documents d JOIN cases c ON d.case_id=c.id "
        "WHERE c.is_demo=0 GROUP BY d.role ORDER BY count DESC", ()
    )
    return [{"role": row["role"], "count": row["count"]} for row in rows]
