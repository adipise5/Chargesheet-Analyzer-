# Graph schema

Graph objects include Case, Document, TextChunk, Person roles, Event, Location, Claim, evidence subtypes, Device, Vehicle, Weapon, and LegalSection. Claims mediate assertions: a witness `MAKES_CLAIM`; a claim points to subjects/events; evidence `SUPPORTS` or `CONTRADICTS` it. Extracted edges carry case/document/page/chunk provenance through citation objects plus confidence, extraction method, and human-verification state.

`SAME_AS` requires strong contextual identifiers. Name similarity alone produces at most `POSSIBLY_SAME_AS`. D1 stores a normalized local graph in SQLite and projects it to generic Neo4j `CaseNode` nodes with relationship-kind properties so schema changes remain migration-friendly.

