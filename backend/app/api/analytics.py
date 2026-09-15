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
def summary(include_reference_records: bool = False):
    """Global statistics across all cases."""
    return global_summary(include_reference_records)


@router.get("/crime-types")
def crime_types(include_reference_records: bool = False):
    """IPC/BNS section frequency distribution."""
    return crime_type_distribution(include_reference_records)


@router.get("/temporal")
def temporal(include_reference_records: bool = False):
    """Cases/events grouped by month for seasonality analysis."""
    return temporal_distribution(include_reference_records)


@router.get("/hotspots")
def hotspots(include_reference_records: bool = False):
    """Crime frequency by police station."""
    return crime_hotspots(include_reference_records)


@router.get("/case-status")
def case_status(include_reference_records: bool = False):
    """Case resolution pipeline status breakdown."""
    return case_status_distribution(include_reference_records)


@router.get("/evidence-profile")
def evidence(include_reference_records: bool = False):
    """Evidence type distribution."""
    return evidence_profile(include_reference_records)


@router.get("/entity-network")
def entities(include_reference_records: bool = False):
    """Top entities appearing across multiple cases."""
    return entity_network(include_reference_records)


@router.get("/findings-summary")
def findings(include_reference_records: bool = False):
    """Finding type distribution."""
    return findings_summary(include_reference_records)


@router.get("/document-roles")
def doc_roles(include_reference_records: bool = False):
    """Document role distribution."""
    return document_roles(include_reference_records)
