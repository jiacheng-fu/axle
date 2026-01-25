# Copilot / AI Agent Instructions — tamuhack26

This file gives focused, actionable guidance for AI coding agents working in this repository.

## Big picture
- Backend: FastAPI app in `backend/main.py` that includes `routes/compare.py`.
- Frontend: Vite + React app in `frontend/` (entry: `frontend/src/App.jsx`).
- Scraping & data: `data/scrape_vdp.py` collects VDP pages and appends to `data/carData.json`.
- AI: `backend/services/aiRecommendation.py` calls OpenAI via `OPENAI_API_KEY`.

Data flow: frontend calls the backend `POST /compare` endpoint with VINs → backend decodes VINs via NHTSA scraper → computes age → calls AI service to generate `ai_summary` → returns `{ cars, ai_summary }`.

## Critical developer workflows
- Start backend (development): run a Uvicorn server pointed at the FastAPI app. Example:

  uvicorn backend.main:app --reload --port 8001

- Start frontend (development):

  cd frontend
  npm install
  npm run dev

- Scrape a single VDP page (writes/update `data/carData.json`):

  python data/scrape_vdp.py <vehicle_detail_url>

## Important conventions & gotchas discovered in code
- API contract mismatch: `frontend/src/hooks/useCompareCars.js` POSTS `{ vins }` (an object). `backend/routes/compare.py` declares `def compare_vins(vins: list[str])` (expects a raw list). Either:
  - Update frontend to `body: JSON.stringify(vins)` (send JSON array), or
  - Update backend to accept a dict (`{ "vins": [...] }`) or a Pydantic model.

- Module filename vs import name mismatches: backend imports use snake_case names (`scrapers.nhtsa_decoder`, `scrapers.vin_utils`) but actual files are named with camelCase (`nhtsaDecoder.py`, `vinUtil.py`). Be careful: these will raise ImportError on runtime. Fix by renaming files or adjusting imports.

- Optional Playwright usage: `data/scrape_vdp.py` will try Playwright as a fallback. Playwright is optional; scraping will still work via `requests` for many sites. The script writes `debug_page.html` on parse failure for inspection.

## External dependencies (inferred from imports)
- Backend/runtime: `fastapi`, `uvicorn`, `requests`, `python-dotenv`, `openai` (new-style client: `from openai import OpenAI`), `beautifulsoup4`, `lxml`, optionally `playwright`.
- Frontend: `react`, `react-dom`, `vite` (see `frontend/package.json`).

Add missing dependencies to `backend/requirements.txt` if you update environment automation.

## Small, concrete examples for edits
- To make frontend/backend work end-to-end quickly: change the frontend POST to send a raw array. Edit `frontend/src/hooks/useCompareCars.js`:

  const res = await fetch("http://localhost:8001/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(vins) // <-- send array, not { vins }
  });

- Or change backend signature in `backend/routes/compare.py` to:

  def compare_vins(payload: dict):
      vins = payload.get("vins", [])

and validate with Pydantic when hardening.

## Where to look first when debugging
- Runtime import errors: check `backend/scrapers/` filenames vs imports in `backend/routes/compare.py`.
- Missing environment keys: `OPENAI_API_KEY` is required for `backend/services/aiRecommendation.py`.
- Empty `backend/requirements.txt`: install inferred packages above or add them to the file.

## When making changes
- Preserve the simple JSON shape returned by `compare`: `{ "cars": [...], "ai_summary": "..." }` — frontend expects `data.cars` and `data.ai_summary`.
- Keep the frontend's fallback demo block in `frontend/src/App.jsx` intact when working on UX; it helps local dev when backend is offline.

---
If anything above is unclear or you want the file to include command snippets for Windows PowerShell (or a requirements.txt update), tell me which area to expand and I'll update the instructions.
