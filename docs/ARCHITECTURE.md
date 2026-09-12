# Architecture

D1 is a modular monolith optimized for a 16 GB Apple Silicon laptop. FastAPI owns ingestion, provenance, graph construction, retrieval, analysis, audit, and a stable provider boundary. React is a desktop-first investigation client. SQLite is authoritative for cases, jobs, pages, chunks, graph objects/edges, reviews, findings, and operational audit events. Original files and rendered derivatives live under per-case UUID directories. Neo4j is a local projection for graph traversal when configured.

The key interfaces are `OCRProvider`, `EmbeddingProvider`, `GraphRepository`, and `DocumentStorage`. `OllamaService` is the D1 local LLM adapter. These boundaries allow a future internal GPU deployment without changing extraction or UI contracts.

Failure is explicit and partial processing is preserved. Native PDFs can process without Tesseract. Lexical and graph retrieval remain usable without embeddings. A missing Qwen model never triggers an external request.

