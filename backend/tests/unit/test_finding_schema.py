import pytest
from pydantic import ValidationError

from app.schemas.finding import Finding


def test_verified_finding_requires_citation():
    with pytest.raises(ValidationError):
        Finding(id="f", type="strong_point", title="x", summary="y", classification="STRONGLY_CORROBORATED", confidence=.8, verified=True)


def test_source_backed_finding_validates():
    finding = Finding(id="f", type="strong_point", title="x", summary="y", classification="STRONGLY_CORROBORATED", confidence=.8,
                      verified=True, supporting_sources=[{"document_id": "d", "page": 1, "chunk_id": "c", "label": "p1"}])
    assert finding.verified

