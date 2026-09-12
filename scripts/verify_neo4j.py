"""Project the synthetic graph into an explicitly configured local Neo4j and verify counts."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings  # noqa: E402
from app.graph.repository import graph_repository  # noqa: E402
from app.services.demo_service import DEMO_CASE_ID, load_demo_case  # noqa: E402
from app.storage.sqlite import db  # noqa: E402


def main() -> None:
    if not settings.neo4j_enabled:
        raise SystemExit("Set NEO4J_ENABLED=true and a local NEO4J_URI")
    db.initialize()
    load_demo_case()
    graph = graph_repository.data(DEMO_CASE_ID)
    objects = [{"id": node["id"], "kind": node["type"], "subtype": node["metadata"].get("subtype", node["type"].lower()),
                "label": node["label"], "confidence": node["confidence"], "data": node["metadata"]} for node in graph["nodes"]]
    relations = [{"id": edge["id"], "case_id": DEMO_CASE_ID, "source_id": edge["source"], "target_id": edge["target"],
                  "relation": edge["relation"], "confidence": edge["confidence"], "citations": edge["citations"],
                  "extraction_method": edge["extraction_method"], "human_verified": edge["human_verified"]} for edge in graph["edges"]]
    graph_repository.replace_case(DEMO_CASE_ID, objects, relations)
    from neo4j import GraphDatabase
    auth = (settings.neo4j_user, settings.neo4j_password) if settings.neo4j_password else None
    with GraphDatabase.driver(settings.neo4j_uri, auth=auth) as driver:
        driver.verify_connectivity()
        record = driver.execute_query(
            "MATCH (n:CaseNode {case_id:$case_id}) OPTIONAL MATCH (n)-[r:RELATED]->() RETURN count(DISTINCT n) AS nodes,count(DISTINCT r) AS edges",
            case_id=DEMO_CASE_ID,
        ).records[0]
    print(f"Neo4j projection verified: {record['nodes']} nodes, {record['edges']} relationships")
    if record["nodes"] < 20 or record["edges"] < 10:
        raise SystemExit("Neo4j projection counts are below the expected synthetic graph")


if __name__ == "__main__":
    main()
