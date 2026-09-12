# API

FastAPI publishes OpenAPI at `/docs`. Major routes match the D1 brief: `/api/cases`, case documents/process/status, overview/findings/timeline/evidence/graph, page provenance, OCR review, and query. `POST /api/demo` creates the idempotent synthetic case. `GET /api/system/health` reports local service readiness without sending case data.

Errors use an HTTP status plus a stable code/message object for guarded uploads and request validation. Query responses contain `answer`, `citations`, `graph_paths`, `confidence`, `review_required`, and retrieval diagnostics.

