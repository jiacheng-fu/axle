# CarScout

AI-powered used-car shopping. Describe what you want in plain English, and
CarScout finds, ranks, and compares real listings from nearby dealers.

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
