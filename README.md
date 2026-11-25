# Axle

*Formerly CarScout — renamed August 2026. Infrastructure names keep the old name
(the `carscout` stack, `CARSCOUT_*` env vars, the `carscout-listings-cache` table,
the `CarScoutApi`/`CarScoutFunction` resources) so the deployed resources stay intact.*

## Live

- App: https://d1j3m9qdbgs5ik.cloudfront.net

### Architecture

    CloudFront + S3 (React/Vite SPA)
            |
            v
    API Gateway (HTTP API) -> Lambda (FastAPI via Mangum, python3.12, arm64)
            |
            +-- DynamoDB  carscout-listings-cache   shared listing cache, native TTL
            +-- Supabase  auth + saved vehicles
            +-- Auto.dev  live inventory (1,000 calls/month free tier)

The listing cache is three tiers: in-process memory (900s) -> DynamoDB (shared,
30d) -> local disk -> Auto.dev. On Lambda the disk tier lives in /tmp, which is
per-instance and wiped on cold start; DynamoDB is what actually protects the
monthly API quota across invocations.

### Deploying

    # API
    pip install -r backend/requirements.txt --platform manylinux2014_aarch64         --implementation cp --python-version 3.12 --only-binary=:all: --target build_pkg
    cp backend/*.py build_pkg/ && cp -r data build_pkg/data
    sam deploy --stack-name carscout --resolve-s3 --capabilities CAPABILITY_IAM

    # Frontend
    cd frontend && npm run build
    aws s3 sync dist/ s3://carscout-web-<account-id>/ --delete

One-time table setup: `python backend/create_cache_table.py`

AI-powered used-car shopping. Describe what you want in plain English, and
Axle finds, ranks, and compares real listings from nearby dealers.

> Originally a TAMUhack proof-of-concept (hardcoded to a single Toyota
> dealership), now being rebuilt into a real, deployed, nationwide product.
> See **[docs/ROADMAP.md](docs/ROADMAP.md)** for the architecture and plan.

## How it works

A chat-style UI collects your zip code and preferences. The backend uses an LLM
to turn natural language into structured preferences, then scores and ranks
inventory and generates AI-powered comparisons between vehicles.

## Tech stack

- **Frontend:** React 18 + Vite (`frontend/`)
- **Backend:** FastAPI + OpenRouter LLM (`backend/`)
- **Data (current):** static `data/carData.json`
- **Data (target):** Supabase Postgres, fed by an ingestion pipeline
  (Auto.dev listings + NHTSA VIN decode + LLM enrichment) — see the roadmap.

## Local development

Prerequisites: **Node ≥ 18**, **Python ≥ 3.11**.

### Backend

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # then add your OPENROUTER_API_KEY
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_BASE defaults to http://localhost:8000
npm run dev
```

Then open the Vite dev URL (default http://localhost:5173).

> `npm start` (from `frontend/`) runs the frontend and backend together via
> `concurrently`.

## Project structure

```
backend/     FastAPI app (preference extraction, scoring/ranking, compare)
frontend/    React + Vite chat UI
data/        carData.json + scrapers (being replaced by the ingestion pipeline)
docs/        ROADMAP.md and design notes
```

## Status

Active rebuild. The current `main` still runs on the static demo dataset while
the Supabase-backed ingestion pipeline is built out per the roadmap.
