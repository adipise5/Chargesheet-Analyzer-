from app.extraction.entity_resolution import normalize_entity, normalize_text, resolution_decision


def test_unicode_and_whitespace_normalization_preserves_gujarati():
    assert normalize_text("રવિ\u200d   પટેલ\n\n\nX") == "રવિ પટેલ\n\nX"


def test_entity_normalization():
    assert normalize_entity("Ravi  Patel") == "ravipatel"


def test_uncertain_names_do_not_auto_merge():
    relation, confidence = resolution_decision({"label": "Ravi Patel"}, {"label": "Ravibhai Patel"})
    assert relation != "SAME_AS"
    assert 0 <= confidence <= 1

