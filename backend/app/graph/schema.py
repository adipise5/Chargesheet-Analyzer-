NODE_TYPES = {
    "Case", "Document", "Page", "TextChunk", "Person", "Accused", "Victim", "Complainant",
    "Witness", "PoliceOfficer", "Event", "Location", "Claim", "Evidence", "DigitalEvidence",
    "PhysicalEvidence", "ForensicEvidence", "Device", "Vehicle", "Weapon", "LegalSection",
}
RELATION_TYPES = {
    "PART_OF", "MENTIONED_IN", "SOURCE_OF", "MAKES_CLAIM", "SUPPORTS", "CONTRADICTS",
    "INVOLVES", "SUBJECT_OF", "ABOUT_EVENT", "PRESENT_AT", "OCCURRED_AT", "OCCURRED_ON",
    "OWNS", "USES", "SEIZED_FROM", "RECOVERED_FROM", "CAPTURED_BY", "CONNECTED_TO",
    "HAS_EVIDENCE", "RELATES_TO", "ACCUSED_OF", "REFERENCES_SECTION", "SAME_AS", "POSSIBLY_SAME_AS",
}


def validate_relation(source: str, target: str, relation: str, citations: list[dict]) -> None:
    if relation not in RELATION_TYPES:
        raise ValueError(f"Unsupported relation: {relation}")
    if not source or not target:
        raise ValueError("Graph relationship endpoints are required")
    if relation not in {"PART_OF", "SAME_AS", "POSSIBLY_SAME_AS"} and not citations:
        raise ValueError("Source provenance is required for extracted graph relationships")

