# Render free demo deployment

This branch contains a separate deployment mode for a public demonstration. It
serves a precomputed SQLite snapshot and the built React interface from one
Render web service. It does not install or call Ollama, Tesseract, BGE-M3, or
Neo4j at runtime.

## What is and is not live

The hosted service is intentionally read-only. Overview, analysis, defense,
precedent, evidence, timeline, graph, documents, analytics, and Ask Case all
read the snapshot. Ask Case first uses the small set of locally precomputed demo
answers and otherwise returns a clearly labelled source-only answer. Uploads,
OCR correction, new cases, judgment import, processing, and purge are disabled.

The database and filesystem on Render free are ephemeral. A restart or redeploy
can discard runtime changes, which is acceptable here because the image seeds
the snapshot again at startup. This is a demo architecture, not a production
case-record store.

## Prepare a public-only snapshot locally

Use the normal local app to process only public or synthetic material. The
repeatable public-demo importer stages outside the active `data/` directory,
adds the five verified public judgment examples as separate incomplete source
cases, warms their reusable outputs, and exports the audited six-case bundle:

```bash
python scripts/import_public_demo.py --replace
```

The same scripts run on Windows PowerShell:

```powershell
.venv\Scripts\python.exe scripts\import_public_demo.py --replace
```

The exporter copies the database, case document files, and legal corpus into a
portable bundle. Inspect `manifest.json`, the copied filenames, and the database
counts before using it. Never put private FIRs, chargesheets, OCR images, or
local runtime databases in `demo_snapshot/` or commit them. The repository ignores that
directory by default as a safety measure.

This deployment branch contains a deliberately audited public-only six-case
bundle in `demo_snapshot/`. The ignore rule remains a guard against accidental
additions; if the snapshot is regenerated, review the manifest, source report,
filenames, and Git diff before force-adding the replacement. Keep private local
runtime data in `data/`, where it remains ignored.

## Deploy

Account setup requires no API key for this workflow. Log in to Render and
authorize its GitHub integration to access `adipise5/Chargesheet-Analyzer-`.
Choose branch `prishiv_render_demo`, repository root, Docker runtime and the
Free instance. No external database, model service, disk or secret is needed.
The Blueprint alternative uses `render.yaml` on that same branch.
If the account requests payment verification, stop; this project does not
require a paid plan or permission to supply payment details.

See [public sources and demonstration limits](DEMO_SOURCES.md).

1. Push this branch to GitHub after reviewing the privacy checks.
2. In Render, create a new Blueprint from the repository and select
   `render.yaml`, or create a Docker web service using the repository root.
3. Keep the service on the Free plan. The Blueprint sets `APP_ENV=render_demo`,
   binds the container to `0.0.0.0`, and uses Render's supplied `PORT`.
4. Wait for the health check at `/health`, then open the service URL.

Render free services sleep after inactivity and wake on the next request. The
first request after sleep may take longer; it should not trigger model
inference. If the snapshot is absent, the service still boots as an empty
read-only UI, which makes this mistake visible rather than silently using local
data.

## Local verification of the image

With Docker installed, build and run the exact hosted mode locally:

```bash
docker build -t chargesheet-render-demo .
docker run --rm -p 10000:10000 chargesheet-render-demo
```

Open `http://127.0.0.1:10000`. The dashboard should say “Hosted snapshot ·
read-only”; no model health check should be required, mutation controls should
be hidden, and `/health` should report `read_only: true`.

The regular local workflow is unchanged: Vite remains on `127.0.0.1:5173`, the
API remains on `127.0.0.1:8000`, and local processing continues to use the
approved local Ollama/Tesseract/optional Neo4j services.
