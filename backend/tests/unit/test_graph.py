import pytest

from app.graph.provenance import citations_are_valid
from app.graph.schema import validate_relation


def test_extracted_edge_requires_provenance():
    with pytest.raises(ValueError):
        validate_relation("claim", "event", "ABOUT_EVENT", [])


def test_valid_provenance():
    citation = {"document_id": "d", "page": 1, "chunk_id": "c", "label": "source"}
    validate_relation("claim", "event", "ABOUT_EVENT", [citation])
    assert citations_are_valid([citation], {"c"})
    assert not citations_are_valid([{**citation, "chunk_id": "missing"}], {"c"})

