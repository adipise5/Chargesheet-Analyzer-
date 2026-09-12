"""Cross-case analytics API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.analytics_service import (
    case_status_distribution,
    crime_hotspots,
    crime_type_distribution,
    document_roles,
    entity_network,
    evidence_profile,
    findings_summary,
    global_summary,
    temporal_distribution,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def summary():
    """Global statistics across all cases."""
    return global_summary()


@router.get("/crime-types")
def crime_types():
    """IPC/BNS section frequency distribution."""
    return crime_type_distribution()


@router.get("/temporal")
def temporal():
    """Cases/events grouped by month for seasonality analysis."""
    return temporal_distribution()


@router.get("/hotspots")
def hotspots():
    """Crime frequency by police station."""
    return crime_hotspots()


@router.get("/case-status")
def case_status():
    """Case resolution pipeline status breakdown."""
    return case_status_distribution()


@router.get("/evidence-profile")
def evidence():
    """Evidence type distribution."""
    return evidence_profile()


@router.get("/entity-network")
def entities():
    """Top entities appearing across multiple cases."""
    return entity_network()


@router.get("/findings-summary")
def findings():
    """Finding type distribution."""
    return findings_summary()


@router.get("/document-roles")
def doc_roles():
    """Document role distribution."""
    return document_roles()
