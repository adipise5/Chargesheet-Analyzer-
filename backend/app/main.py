from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, analytics, cases, documents, graph, judgments, processing, query, review, system
from app.core.config import settings
from app.core.logging import configure_logging
from app.storage.sqlite import db


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
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
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
for router in (cases.router, documents.router, judgments.router, processing.router, analysis.router, analytics.router, graph.router, query.router, review.router, system.router):
    app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": {"errors": exc.errors()}}})


@app.get("/health")
def root_health():
    return {"status": "ok"}

