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

> A personal project, deployed as a live nationwide product.
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

## Use Axle from an AI agent (MCP)

`axle_mcp/` is a [Model Context Protocol](https://modelcontextprotocol.io) server, so
agents such as Claude Code, Claude Desktop and Cursor can call Axle directly:
"find me an AWD SUV under $25k near 77840 and estimate the payment" becomes tool calls
against Axle's ranking engine.

| Tool | What it does |
|---|---|
| `search_used_cars` | Ranked listings near a zip code from structured filters (makes, models, years, budget, mileage, body type, drivetrain, colors, features). Reports any constraints Axle had to relax. |
| `find_dealers` | Dealers near a zip code, nearest first, with listing counts. |
| `estimate_monthly_payment` | Axle's loan formula with credit-score APR bands. |

All three are read-only.

### Setup

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r axle_mcp/requirements.txt

# Claude Code
claude mcp add axle -- "$(pwd)/backend/.venv/bin/python" "$(pwd)/axle_mcp/server.py"
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "axle": {
      "command": "/absolute/path/to/axle/backend/.venv/bin/python",
      "args": ["/absolute/path/to/axle/axle_mcp/server.py"]
    }
  }
}
```

With no configuration, the server runs Axle's ranking in-process over the bundled demo
inventory: no network and no keys. To search live inventory, set `AXLE_API_URL` to a
deployed Axle API (https only).

### How it is built

- **No model calls per search.** The agent is already a language model, so it turns plain
  English into filters itself. The server sends Axle structured preferences on the API path
  that ranks them as-is, which skips Axle's own extraction call.
- **The live quota is protected.**
  - Identical searches are cached for 15 minutes.
  - Each tool is limited to 20 calls a minute.
  - Local mode is pinned to the demo inventory, so it can never spend the listings quota by
    accident.
- **Dealer text is treated as untrusted.** A tool result goes straight into the agent's
  context, and listing text is written by third-party dealers.
  - The server returns an allowlist of fields only. Free-text dealer notes, spec sheets and
    images are never sent.
  - Short fields are stripped of invisible and bidirectional-override characters.
  - Any field that reads like an instruction ("ignore previous instructions", role tags,
    links) is withheld, and the result says how many fields were withheld.
- **Inputs are validated** before anything reaches Axle: 5-digit zip, bounded radius, years,
  prices and list sizes.

### Tests

```bash
backend/.venv/bin/python -m pytest axle_mcp/tests -q
```

The suite has 39 tests, and none of them need network access or API keys. It covers:
- ranking on the demo inventory;
- input validation;
- a poisoned listing whose injected text must not reach the agent;
- a negative control: all 2,983 feature strings in the real inventory pass the screen untouched;
- cache and rate-limit behaviour, using a fake clock;
- the live-API path, against a mocked transport;
- an end-to-end run that launches the server over stdio the way an MCP client does.

## Project structure

```
backend/     FastAPI app (preference extraction, scoring/ranking, compare)
frontend/    React + Vite chat UI
axle_mcp/    MCP server: Axle's search and ranking as tools for AI agents
data/        carData.json + scrapers (being replaced by the ingestion pipeline)
docs/        ROADMAP.md and design notes
```

## Status

Active rebuild. The current `main` still runs on the static demo dataset while
the Supabase-backed ingestion pipeline is built out per the roadmap.
