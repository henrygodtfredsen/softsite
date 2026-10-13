# CLAUDE.md — project conventions

**Read first, every session:** `PROJECT_BRIEF.md` (spec, source of truth), `PROGRESS.md` (status, open questions), then `docs/PLAN.md` and `docs/DATA_SOURCES.md` as needed.

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
- Polite UA `sc-site-screener/0.1 (academic research project)`, ≤1 req/s, cache everything under `data/raw/<source>/<YYYY-MM-DD>/`.
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
- **Parcel universe:** City `RegionalBaseOpenData/7`, `LNDPARSTATUS='A'`, `PARTYPE='LND'`, dissolved by APN.
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
- Small commits with clear messages. The repo will be public.
- Commit identity: set per Bodie's choice (pending as of Phase 0).
