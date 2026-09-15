# Render free demo image: the React bundle and the precomputed case snapshot
# are served by one small FastAPI process. No Ollama, Tesseract, or Neo4j is
# installed in this image.
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    APP_ENV=render_demo \
    APP_HOST=0.0.0.0 \
    DEMO_SNAPSHOT_MODE=true \
    DEMO_SNAPSHOT_DIR=/app/demo_snapshot
WORKDIR /app

COPY backend/requirements-render.txt /app/backend/requirements-render.txt
RUN pip install --no-cache-dir -r /app/backend/requirements-render.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist/ /app/frontend/dist/
COPY demo_snapshot/ /app/demo_snapshot/
RUN mkdir -p /app/data/cases

EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
