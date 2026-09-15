from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import analysis, analytics, cases, documents, graph, judgments, processing, query, review, system
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.runtime_mode import ReadOnlyDemoError
from app.services.snapshot_service import seed_snapshot
from app.storage.sqlite import db


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
    seed_snapshot(settings, db.path)
    settings.ensure_directories()
    db.initialize()
    yield


app = FastAPI(
    title="Gujarat Police Chargesheet Intelligence",
    version="1.0.0-d1",
    description="Offline-first, provenance-preserving chargesheet decision support",
    lifespan=lifespan,
)
configure_logging()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.render_demo else [settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
for router in (cases.router, documents.router, judgments.router, processing.router, analysis.router, analytics.router, graph.router, query.router, review.router, system.router):
    app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": {"errors": exc.errors()}}})


@app.exception_handler(ReadOnlyDemoError)
async def read_only_demo_error(_: Request, exc: ReadOnlyDemoError):
    return JSONResponse(status_code=403, content={"detail": {"code": "READ_ONLY_DEMO", "message": str(exc)}})


@app.get("/health")
def root_health():
    return {"status": "ok", "mode": "render_demo" if settings.render_demo else "local",
            "read_only": settings.render_demo, "models_required": not settings.render_demo}


# A Render container serves the already-built React application and API from
# one origin. Vite remains the local development server when this is false.
frontend_dist = Path(os.getenv("FRONTEND_DIST", str(settings.root_dir / "frontend" / "dist")))
if settings.render_demo or os.getenv("SERVE_FRONTEND", "false").lower() == "true":
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

