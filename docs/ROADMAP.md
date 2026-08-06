# Axle (formerly CarScout) — Architecture & Deployment Roadmap

From a hardcoded hackathon demo → a real, deployed, **nationwide, multi-dealer**
product on a **$0 / free-tier** budget (Supabase + Vercel).

---

## 1. Where we started (the demo) vs. where we're going

**The demo was hardcoded for the judges:**
- One dealership ("College Station Toyota"), its inventory only.
- Scraper tuned to that one dealer's website.
- Static `data/carData.json` (162 Toyotas) re-read on every request.
- Cars were pre-tagged by hand to feed the matcher.
- Backend keeps a single module-global `state` shared across all requests.
- Toyota-only substitute tables, single hardcoded dealership object, etc.

**The product (target):** enter any US zip → search real inventory from nearby
dealers nationwide → fill missing specs/features automatically → rank against the
user's natural-language preferences → compare any two cars. No hardcoding, no
fake data, works for any user.

---

## 2. Existing code we keep vs. replace

**Keep (the genuinely good parts):**
- `POST /preferences` LLM preference extraction (natural language → structured prefs).
- The scoring/ranking engine + constraint relaxation (reads listings, scores them).
- `POST /compare` and `POST /compare-chat` LLM endpoints.
- The whole React chat UI (`frontend/`).

**Replace / remove:**
- Static `carData.json` as the data source → live Supabase-backed inventory.
- Single-dealership + Toyota-substitute hardcoding → real multi-dealer data.
- Module-global `state` → stateless (mandatory for serverless).
- Hand-tagged features → automated VIN + LLM enrichment.
- Dealer-specific scraper → a generalized ingestion pipeline.

---

## 3. Target architecture (decided)

```
            ┌──────────────────────────────────────────────┐
            │              Vercel project                   │
            │   React SPA (Vite)  ──/api──►  FastAPI         │
            │   served static       (same   serverless fns  │
            │                       origin)                 │
            └───────────────┬───────────────────┬───────────┘
                            │ SQL                │ ingestion (cache-first)
                            ▼                    ▼
                  ┌───────────────────┐   ┌─────────────────────────────┐
                  │ Supabase Postgres │   │  INGESTION PIPELINE          │
                  │ listings, dealers │   │  1. Acquire  2. Enrich       │
                  │ trim_enrichment   │◄──│  3. Normalize 4. Upsert      │
                  │ vin_cache, search │   └──────────┬──────────────────┘
                  │ _cache (+Auth pv) │              │
                  └───────────────────┘    ┌─────────┴──────────┐
                                           ▼                    ▼
                              free data sources:        gap-fill (free):
                              • Auto.dev Listings        • NHTSA vPIC (VIN→specs)
                                (1k calls/mo free,       • LLM by year/make/
                                 nationwide, VIN+price)    model/trim (cached)
                              • [fallback] Google Places
                                + generic JSON-LD scraper
```

- **Frontend + API share one Vercel domain** → no CORS; `VITE_API_BASE = /api`.
- **Backend (FastAPI as Vercel Python functions)** keeps scoring + LLM, but reads
  inventory from Supabase. `backend/main.py` wrapped by `api/index.py`;
  `vercel.json` routes `/api/*`. Global `state` removed.
- **Supabase Postgres** is the source of truth for inventory + caches (+ Auth later).

---

## 4. The ingestion pipeline (the heart of the rebuild)

When a user searches a zip, the backend serves **cache-first**, fetching fresh
data only on a miss:

**1. Acquire — get real listings near the zip**
- Primary: **Auto.dev Vehicle Listings API** (free Starter: 1,000 calls/mo, 20
  results/call, nationwide US dealers). Search by `zip` + `distance` + filters;
  returns VIN, price, mileage, dealer, etc. Photos via Auto.dev Vehicle Photos.
- Fallback (no/low coverage, or to reduce API usage): **Google Places API**
  (free per-SKU cap) to find nearby dealer sites → generic scraper that extracts
  `schema.org/Vehicle` JSON-LD and `sitemap.xml` VDP pages. This is the
  long-term differentiator and the path when no VIN is available.

**2. Enrich — fill the gaps (your VIN method)**
- **VIN present** → decode via **NHTSA vPIC** (free, unlimited) for hard specs
  (trim, engine, body, drivetrain, etc.). Then an **LLM call keyed on
  `year + make + model + trim`** fills soft/marketing features ("heated seats",
  "sunroof"…). **Cache the result in `trim_enrichment`** so each unique trim is
  looked up once and reused across every car of that trim — keeps LLM volume tiny.
- **No VIN** → best-effort from the source page + the same LLM-by-trim lookup.

**3. Normalize** every source into the one canonical `listings` shape.

**4. Upsert** into Supabase (dedupe by VIN); record the search in `search_cache`
so repeat searches of the same area cost **zero** API calls until TTL expires.

> **The one honest asterisk:** the free tiers cap *throughput* (Auto.dev 1k
> calls/mo & 20/call; Places free cap). Aggressive caching makes this fine for a
> real, low-traffic product — but scaling to heavy traffic later needs a paid
> plan. This is an operational limit, **not** fake/hardcoded data: any user, any
> US zip, real results. That's the meaningful difference from the demo.

---

## 5. Data model (first cut)

```sql
dealers(id, name, street, city, state, zip, lat, lng, website, source, created_at)

listings(
  vin           text primary key,          -- dedupe key; synth id if VIN missing
  dealer_id     uuid references dealers,
  source        text,                       -- 'autodev' | 'scrape' | ...
  source_url    text, scraped_at timestamptz,
  year int, make text, model text, trim text,
  price_usd int, odometer_miles int,
  exterior_color text, interior_color text,
  body_style text, drivetrain text,
  horsepower_hp int, torque_lbft int,
  engine_type text, transmission text, fuel_type text,
  mpg_city int, mpg_highway int, seating_capacity int,
  features text[],                          -- merged: source + enrichment
  image_urls text[],
  raw jsonb,                                -- full original payload, lossless
  enriched_at timestamptz,
  created_at timestamptz default now(), updated_at timestamptz default now()
)  -- indexes: (make,model), price_usd, body_style, year, dealer_id

trim_enrichment(                            -- LLM/spec cache, one row per trim
  id uuid pk, year int, make text, model text, trim text,
  features text[], specs jsonb, source text, created_at,
  unique(year, make, model, trim)
)
vin_cache(vin pk, decoded jsonb, created_at)         -- NHTSA results
search_cache(id pk, zip text, radius int, filters jsonb, fetched_at, ttl)

-- post-v1 (auth):
profiles(id uuid pk = auth.users.id, email, created_at)
saved_searches(id pk, user_id, query_text, prefs jsonb, created_at)
saved_vehicles(id pk, user_id, vin, created_at)
```

---

## 6. Phased roadmap (v1 = deployed, nationwide, free)

### Phase 0 — Repo hygiene  *(fast, low-risk)*
- Untrack `__pycache__/`; fill empty `backend/requirements.txt`; add
  `.env.example` files; rewrite README; delete the stale `copilot-instructions.md`.

### Phase 1 — De-hardcode the backend
- Remove module-global `state`; `/preferences` uses only `payload.state`.
- Rip out single-dealership + Toyota-substitute hardcoding.
- Put inventory access behind a `repository` interface (JSON now → Supabase next).
- CORS origins via env (mostly moot once same-origin on Vercel).

### Phase 2 — Supabase schema
- Create project; migrations for the tables in §5; seed `dealers`.

### Phase 3 — Ingestion pipeline
- **3a** Auto.dev client → normalize → upsert `listings`; `search_cache` TTL logic.
- **3b** Enrichment: NHTSA vPIC VIN decode (`vin_cache`) + LLM trim lookup
  (`trim_enrichment`), merged into `listings.features`.
- **3c** Point `/preferences` at Supabase (cache-first; fetch-on-miss triggers 3a/3b).

### Phase 4 — Generalized scraper fallback
- Google Places dealer discovery + generic JSON-LD / sitemap extractor → same
  normalize/enrich/upsert path. Handles no-VIN and uncovered dealers.

### Phase 5 — Deploy (**v1 milestone**)
- `api/index.py` + `vercel.json`; env vars in Vercel; frontend → `/api`.
- Deploy; end-to-end smoke test on the live URL.

### Phase 6 — Post-v1
- Supabase Auth + saved searches/favorites (RLS).
- Scheduled refresh job (GitHub Actions cron) to keep inventory warm.
- CI (lint/build), error monitoring, unit tests for the scorer, broaden scraper.

---

## 7. Decisions  *(as of 2026-05-30)*
- ✅ **Hosting:** one Vercel project (SPA + Python serverless API) + Supabase.
- ✅ **Budget:** free-tier only. Backbone = Auto.dev free (1k/mo) + NHTSA (free)
  + Google Places free cap + cached LLM; caching makes it viable.
- ✅ **Enrichment:** VIN-first — NHTSA decode, then LLM by exact trim (cached);
  scraper hybrid as fallback when no VIN.
- ✅ **Geo:** nationwide (Auto.dev is nationwide). Accepted asterisk = free-tier
  throughput caps, mitigated by caching.
- ✅ **v1 scope:** deployed working product (Phases 0–5); Auth deferred to Phase 6.
