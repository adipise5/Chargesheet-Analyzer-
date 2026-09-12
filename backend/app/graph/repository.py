from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Iterable

from app.core.config import settings
from app.graph.schema import validate_relation
from app.storage.sqlite import db

logger = logging.getLogger(__name__)


class GraphRepositoryInterface(ABC):
    @abstractmethod
    def replace_case(self, case_id: str, objects: Iterable[dict], relations: Iterable[dict]) -> None:
        raise NotImplementedError

    @abstractmethod
    def data(self, case_id: str) -> dict:
        raise NotImplementedError


class GraphRepository(GraphRepositoryInterface):
    """SQLite system-of-record plus an optional local Neo4j projection."""

    def replace_case(self, case_id: str, objects: Iterable[dict], relations: Iterable[dict]) -> None:
        with db.connect() as con:
            con.execute("DELETE FROM relations WHERE case_id=?", (case_id,))
            con.execute("DELETE FROM objects WHERE case_id=?", (case_id,))
            for item in objects:
                con.execute(
                    "INSERT INTO objects(id,case_id,kind,subtype,label,data_json,confidence) VALUES(?,?,?,?,?,?,?)",
                    (item["id"], case_id, item["kind"], item.get("subtype", item["kind"]), item["label"],
                     json.dumps(item.get("data", {}), ensure_ascii=False), item.get("confidence", 1.0)),
                )
            for rel in relations:
                validate_relation(rel["source_id"], rel["target_id"], rel["relation"], rel.get("citations", []))
                con.execute(
                    "INSERT INTO relations(id,case_id,source_id,target_id,relation,confidence,citations_json,extraction_method,human_verified) VALUES(?,?,?,?,?,?,?,?,?)",
                    (rel["id"], case_id, rel["source_id"], rel["target_id"], rel["relation"], rel["confidence"],
                     json.dumps(rel["citations"], ensure_ascii=False), rel.get("extraction_method", "deterministic"), int(rel.get("human_verified", False))),
                )
        self._project_to_neo4j(case_id)

    def data(self, case_id: str) -> dict:
        nodes = []
        for row in db.all("SELECT * FROM objects WHERE case_id=?", (case_id,)):
            data = json.loads(row["data_json"])
            nodes.append({"id": row["id"], "type": row["kind"], "label": row["label"],
                          "aliases": data.get("aliases", []), "confidence": row["confidence"], "metadata": data})
        edges = []
        for row in db.all("SELECT * FROM relations WHERE case_id=?", (case_id,)):
            edges.append({"id": row["id"], "source": row["source_id"], "target": row["target_id"],
                          "relation": row["relation"], "confidence": row["confidence"],
                          "citations": json.loads(row["citations_json"]),
                          "extraction_method": row["extraction_method"], "human_verified": bool(row["human_verified"])})
        return {"nodes": nodes, "edges": edges}

    def _project_to_neo4j(self, case_id: str) -> None:
        if not settings.neo4j_enabled and not settings.require_neo4j:
            return
        try:
            from neo4j import GraphDatabase
            graph = self.data(case_id)
            auth = (settings.neo4j_user, settings.neo4j_password) if settings.neo4j_password else None
            with GraphDatabase.driver(settings.neo4j_uri, auth=auth) as driver:
                driver.verify_connectivity()
                with driver.session() as session:
                    session.run("MATCH (n {case_id:$case_id}) DETACH DELETE n", case_id=case_id)
                    for node in graph["nodes"]:
                        session.run(
                            "MERGE (n:CaseNode {id:$id}) SET n.case_id=$case_id,n.type=$type,n.label=$label,n.confidence=$confidence",
                            id=node["id"], case_id=case_id, type=node["type"], label=node["label"], confidence=node["confidence"],
                        )
                    for edge in graph["edges"]:
                        session.run(
                            "MATCH (a:CaseNode {id:$source}),(b:CaseNode {id:$target}) MERGE (a)-[r:RELATED {id:$id}]->(b) SET r.kind=$kind,r.confidence=$confidence,r.citations=$citations",
                            source=edge["source"], target=edge["target"], id=edge["id"], kind=edge["relation"],
                            confidence=edge["confidence"], citations=json.dumps(edge["citations"], ensure_ascii=False),
                        )
        except Exception as exc:
            if settings.require_neo4j:
                raise RuntimeError(f"Local Neo4j is required but unavailable: {exc}") from exc
            logger.warning("Local Neo4j projection unavailable; graph remains persisted in SQLite")


graph_repository = GraphRepository()
