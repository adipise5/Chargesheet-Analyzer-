# GraphRAG

Retrieval has three independent inputs: graph-seed expansion, BGE-M3 cosine similarity, and token lexical scoring. Reciprocal Rank Fusion combines ranks transparently. Provenance is expanded before a context builder applies a 42,000-character safety ceiling (roughly 8k–12k tokens depending on Gujarati/English mix).

The answer prompt forbids guilt/outcome assessment and outside legal knowledge. Citations are returned as document/page/chunk identifiers. Without retrieval, the system returns insufficient information. Without local Qwen, it returns a clearly identified extractive passage view with citations and `review_required=true`.

