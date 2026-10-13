# CLAUDE.md — project conventions

**Read first, every session:**
1. `PROJECT_BRIEF.md` (spec, source of truth)
2. `PROGRESS.md` (status, open questions)
3. `docs/PLAN.md` (decisions log) and `docs/DATA_SOURCES.md` as needed

**Product name:** SoftSite.

**Repo location:** `~/Projects/softsite`. Keep it there; the Desktop is iCloud-synced, and iCloud breaks `.venv` and `node_modules`.

## Commands
- `uv run pipeline all` — fetch and process everything. Add `--refresh` to re-download today's data.
- `uv run pipeline <parcels|addresses|plan_areas|export>` — run one step.
- `uv run pytest` — pipeline tests.
- `npm --prefix web install`, then `npm --prefix web run dev` — app at http://localhost:3000.
- `npm --prefix web run lint` and `npx --prefix web tsc --noEmit` — checks before committing.

## Next.js 16 note
Read `web/AGENTS.md` and the bundled docs in `web/node_modules/next/dist/docs/` before writing Next.js code; APIs differ from older versions.

## Working agreement (short form; full text in PROJECT_BRIEF.md §3)
- Stop at each phase checkpoint. Summarize, list decisions, and wait for Bodie's approval.
- Never fabricate data. Fake fixtures live only in `fixtures/`, are labeled fake, and are never imported by production code.
- Every UI number must trace to a source URL and a retrieval date.
- Add one or two plain-English sentences to `docs/HOW_IT_WORKS.md` for each non-obvious technical choice.
- Ask before any paid service, signup, or cost. Estimate Anthropic API cost before using it.
- Secrets go only in `.env.local`, which is gitignored.
- Never store or show natural-person owner names.
- Bodie is not a professional engineer. Explain in plain language.

## Data access rules (learned in Phase 0)
- Polite UA `softsite/0.1 (academic research project)`, ≤1 req/s, cache everything under `data/raw/<source>/<YYYY-MM-DD>/`.
- City ArcGIS (Cloudflare WAF) blocks SQL-looking `where` clauses (e.g. `IS NULL`). Always query `where=1=1` and filter locally.
- **Blocked to scripts:**
  - santaclaraca.gov (Akamai)
  - ecode360.com
  - EnviroStor
  - GeoTracker web
  - zillow.com pages (the zillowstatic CSVs work)

  Do NOT attempt to bypass bot protection. These sources go through `data/manual/`, filled by Bodie.
- FEMA `hazards.fema.gov` resets connections from the dev machine. Retry from CI only.
- Do not scrape the County Assessor's per-parcel lookup.
- Drop CEQAnet contact columns (names, emails, phones) at ingest.

## Data conventions
- **Canonical parcel key:** `apn` = 8-digit string (`09708058`). Display it as `097-08-058`. Normalize via one tested function; log unmatched values, never guess.
- **City-only IDs:** 313 condo common areas carry a City-only ID instead of an APN (e.g. `097-90-00A`). Their key is `parcel_key = "CITY-097-90-00A"` and `apn` is null. Every other parcel's key is its APN.
- **Parcel universe:**
  - Mapped: City `RegionalBaseOpenData/7` with `LNDPARSTATUS='A'`, merged by key.
  - Ranked: only `PARTYPE='LND'`.
- **Don't show the City's per-parcel `ZoningURL` / `GenPlanURL`.** They're inconsistent; see `docs/DATA_SOURCES.md` §2.
- **Map colors:** at most 3 categorical colors on the map, plus neutrals. Validate any palette change with the dataviz skill's `validate_palette.js --pairs all`.
- **Projections:**
  - Compute in EPSG:6420 (CA State Plane III, US ft).
  - Serve the map in EPSG:4326.
  - Store GeoParquet in `data/processed/`.

## Stack
- Pipeline: Python 3.11+ via `uv`, run as `uv run pipeline <step>`; geopandas/shapely, duckdb spatial, httpx (retry/backoff), pydantic.
- Web: Next.js App Router + TypeScript + Tailwind + shadcn/ui; MapLibre via react-map-gl; Recharts.
- AI: Anthropic Python SDK, model `claude-sonnet-5-5` (verified 2026-10-13).
- Tests: pytest (pipeline math), Playwright smoke test.

## Git
- Small commits with clear messages. The repo is public: never commit personal data, staff contact details, or secrets.
- Commit identity: Bodie's global git config (GitHub no-reply email).
