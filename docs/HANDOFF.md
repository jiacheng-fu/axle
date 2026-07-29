# CarScout — Session Handoff (continue here after restart)

**Why this file exists:** we installed design skills into `~/.claude/skills/`, but
Claude Code only loads skills at startup. This handoff lets a fresh post-restart
session pick up exactly where we left off — with the skills actually loaded — and
do the frontend rework.

> **First thing to do after restart:** read this file and
> [docs/ROADMAP.md](ROADMAP.md), then start the **frontend rework** described in
> §4 using the installed design skills.

---

## 1. Current status

| Area | State |
|---|---|
| Repo | `jiacheng-fu/CarScout` (public, own repo; `upstream` = original `jason-725/tamuhack26`). Local: `c:\Users\brian\OneDrive\Desktop\CarScout` |
| Phase 0 (hygiene) | ✅ done — `requirements.txt`, `.env.example`s, README, `.gitignore` (+`__pycache__`), removed stale `copilot-instructions.md` |
| Phase 1 (de-hardcode backend) | ✅ done — removed global `state` (now stateless), removed Toyota substitute table, added `backend/repository.py` seam, CORS via `ALLOWED_ORIGINS`. Compiles (`py_compile`); not runtime-tested |
| Design skills | ✅ installed in `~/.claude/skills/` (need this restart to load) |
| **Frontend rework** | ⏳ **NEXT — do this now (with skills loaded)** |
| Backend rebuild (Phases 2–5) | later — Supabase + Auto.dev ingestion. **Don't entangle the frontend with backend specifics that will change.** |

> **Uncommitted:** Phase 0 + Phase 1 changes are on disk but **not committed**.
> The user wants to review before any commit/push. (A restart does not lose disk
> changes.)

---

## 2. The task

> Rework the frontend as much as possible **before** the backend is redone.
> Professional but modern. **NOT** the current 2000s look. **NOT** generic
> gradient "AI slop." Rebrand everything to **CarScout**.

## 3. Chosen design direction — "Showroom Editorial (light)"

- **Theme:** warm light / "paper" base (e.g. `#F7F4EF`), not stark white.
- **Accent:** deep oxblood/automotive-maroon (e.g. `#7A1620`) + strong ink for text.
  A single confident accent, used sparingly — not evenly-distributed timid color.
- **Type:** distinctive **editorial serif display** paired with a clean grotesque
  body. **Avoid** Inter / Roboto / Arial / system fonts / Space Grotesk (the
  `frontend-design` skill explicitly warns against these and against converging on
  Space Grotesk). Good candidates: display = Fraunces / Newsreader / Spectral;
  body = Hanken Grotesk / Geist / Public Sans. Pick something characterful.
- **Feel:** luxury magazine / showroom — generous whitespace, big type, calm,
  unhurried, premium. Editorial layout, not a dashboard.
- **Motion:** one well-orchestrated page-load with staggered reveals beats
  scattered micro-interactions. Respect `prefers-reduced-motion`.
- **Remove:** the floating blur "orbs," the grid background, the bright pure-red
  theme, condensed Oswald headings — these read dated.

Per the `frontend-design` skill: commit to the direction with precision; depth via
texture/grain/layering, not default solid blocks or purple-on-white gradients.

## 4. Frontend rework plan (concrete)

Files under `frontend/`:
- `src/App.jsx` (~990 lines) — main app. **Lots of inline styles** in
  `PaymentMethodSelector`, `FinancingForm`, and the dealership buttons that
  hardcode `rgba(235,0,0,...)` red. Brand strings: `"Redline Scout"`,
  `"Chat with Scout"`, `"Welcome to Redline Scout"`. **Rebrand → CarScout** and
  move inline colors onto the new CSS variables/classes.
- `src/index.css` (~970 lines) — **the theme lives here.** Replace wholesale:
  CSS variables, fonts (`@import` the chosen families), backgrounds, cards,
  buttons, chat bubbles, results cards, comparison panel. Remove `.bg-orb`,
  `.bg-grid`, orb/float keyframes.
- `src/components/`: `BrandHeader.jsx` (hero — says "Redline Scout"),
  `MessageList.jsx`, `Composer.jsx`, `ResultsShell.jsx`, `ComparisonPanel.jsx`,
  `ComparisonInsightPanel.jsx` — restyle to match.
- `src/api/client.js` — leave as-is (API contract). `src/main.jsx`, `index.html`
  (update `<title>`/favicon to CarScout).

**Constraints:**
- Keep the app **functional** — don't break the stage flow
  (`zip → select_dealership → payment_method → prefs → done`) or the
  `sendUserMessage` payload shape. This is a restyle + rebrand, not a rewrite of
  behavior.
- The single hardcoded dealership / zip step still exists (real dealer discovery
  is a later backend phase) — keep it working; just restyle.
- It can't be run/screenshotted easily here; offer to launch the Vite dev server
  (`cd frontend && npm install && npm run dev`) to verify visually, or use the
  `run`/`verify` skills.

## 5. Skills to use (now loaded after restart)

- **`frontend-design`** (Anthropic) — overall aesthetic execution. Primary.
- **`impeccable`** (pbakaus) — design/redesign/polish/critique. May need
  `npm install` inside `~/.claude/skills/impeccable/` to run its tooling.
- **`frontend-design-review`** (Microsoft) — review the result after.
- **`ui-styling` / `design-system` / `design`** (ui-ux-pro-max bundle, `ckm:`
  prefix) — tokens/components if useful.

Invoke via the Skill tool (or `/frontend-design`, etc.). If a skill still doesn't
appear, check `~/.claude/skills/<name>/SKILL.md` has `name:`+`description:`
frontmatter (verified at install time).

## 5b. Deferred (intentionally not built yet)
- **Hero landing page.** CarScout should open on a marketing **hero landing page**,
  not drop straight into the tool. Deferred until **after Supabase + user accounts**
  (so the landing page can include sign-in / saved searches). For now the app opens
  directly on the map-based location picker (Step 1). Revisit in/after Phase 6.

## 6. Pointers
- Architecture + phased plan: [docs/ROADMAP.md](ROADMAP.md).
- Memory: `~/.claude/projects/.../memory/` (`carscout-project.md`,
  `carscout-data-pipeline` referenced) — auto-loaded each session.
- Backbone decisions (free-tier, Auto.dev + NHTSA + LLM, Vercel + Supabase,
  nationwide) are in the roadmap §7.
