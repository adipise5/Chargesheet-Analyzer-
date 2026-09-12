# Deliverable 1 completion report

## What was implemented

The repository contains the backend ingestion/OCR/graph/retrieval/analysis APIs, React investigation workstation, synthetic demo, security controls, setup scripts, and documentation. Upload validation covers MIME/signature, parser integrity, password state, size, safe names, hashes, and page count. Page text, boxes, confidence, review state, chunks, findings, and graph edges retain provenance. Human corrections preserve original OCR and rebuild derived data.

The UI provides Overview, Analysis, Evidence, Timeline, Graph, Documents, Ask Case, actual processing stages/counts, PDF.js source rendering, citation navigation, graph inspectors, and review editing. Demo findings cover strong/weak points, contradiction, identifier mismatch, and missing annexure linkage without guilt scoring.

## Architecture

FastAPI + SQLite + UUID filesystem storage form the local D1 system of record. PyMuPDF bypasses OCR for native pages; Tesseract `guj+eng` handles scans; uncertain pages can receive a separate local Qwen vision candidate. The claim-centric graph has an optional local Neo4j projection. Retrieval fuses graph, lexical, and BGE-M3 ranks before a bounded local Qwen prompt.

## Detected hardware and models

Apple M4 MacBook Air with 16 GB unified memory. Ollama 0.33.3 is bound to `127.0.0.1:11434`. Selected models are `qwen3.5:4b` and `bge-m3`; both were downloaded and executed. BGE-M3 returned 1,024-dimensional embeddings. Tesseract 5.5.3 plus Gujarati data and Neo4j Community 2026.07.1 are installed.

## How to run and demo

Run `make setup`, `make check`, then `make dev`; open `http://127.0.0.1:5173` and choose **Load Demo Case**. Traverse every case tab, click a finding citation into its exact PDF page, select graph nodes/edges, and ask "What evidence connects A1 with the vehicle?"

## Tests executed

- `make test`: 25 backend unit/API/integration tests passed; frontend ESLint passed; Vite production build passed.
- native synthetic PDF → extraction → graph → findings pipeline passed.
- actual Tesseract `guj+eng` image: correct mixed-language output, 95.11% mean word confidence, 9 word boxes.
- Neo4j localhost projection: 24 nodes and 21 relationships, with telemetry and Fleet discovery disabled.
- model verification: Qwen3.5 4B response plus BGE-M3 1,024-dimensional embedding.
- live browser: demo, five finding classes, Cytoscape graph, PDF rendering, citation-to-page navigation, and 8-citation model-backed GraphRAG response.
- repository scan: runtime HTTP is limited to relative browser API calls and configured local/private Ollama; no hosted inference/storage integration was found.

## Performance observations

The fanless 16 GB machine runs one Qwen request at a time. Cold model load and the first multi-source answer can take roughly 30–90 seconds; BGE batches are capped at 8 and answer generation at 768 tokens. The frontend production bundle succeeds; PDF.js makes the initial JavaScript payload large enough for Vite to emit a non-failing chunk-size warning.

## Known limitations

- Printed Gujarati OCR is verified; handwriting quality remains model/document dependent and always reviewable.
- Deterministic normal-mode extraction is conservative; nuanced Gujarati person/role extraction benefits from local structured LLM enrichment and domain evaluation.
- Neo4j is installed and verified but application projection remains opt-in until an authenticated, telemetry-disabled local configuration is supplied.
- D1 includes no validated statutory corpus, so it extracts cited sections but does not explain or invent law text.
- Production authentication, RBAC, encryption/key management, retention, malware scanning, and immutable audit export belong to deployment hardening.

## Deliverable 2 priorities

Evaluate an approved Gujarati HTR/IndicOCR provider, add domain-labeled extraction evaluation, enrich claim/evidence relation resolution, introduce authenticated multi-user case authorization, and validate migration to internal Linux GPU inference and secured Neo4j infrastructure.
