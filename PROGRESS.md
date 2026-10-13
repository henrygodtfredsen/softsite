# Progress

## Status: Phase 0 complete — waiting at checkpoint for approval (2026-10-13)

## Done
- **Phase 0 recon (2026-10-13).** Every source in the brief was hit live.
  - Findings: `docs/DATA_SOURCES.md`
  - Plan, cost estimate, names, blockers: `docs/PLAN.md`
- **Environment:**
  - Node 24.16, npm 11.13, git 2.39, Homebrew 6.0
  - `uv` 0.13.0 installed via Homebrew during Phase 0
  - System Python is 3.9.6; uv will manage Python 3.12 for the pipeline
- Repo initialized (`main`) with the brief and docs. No application code yet.

## Next (after approval)
- **Phase 1:** pipeline pulls city parcels + zoning; Next.js map with zoning colors, plan outlines, parcel panel, APN/address search; deploy to Vercel.

## Open questions for Bodie
See the "Decisions needed" list at the Phase 0 checkpoint (also in `docs/PLAN.md` §8).
1. Git commit identity (name + email, or GitHub no-reply email)
2. Install `gh` and sign in; approve a free Vercel account
3. PD parcels: use the General Plan density as a proxy? (`docs/PLAN.md` §4)
4. Existing-building method + floor-height defaults (`docs/PLAN.md` §3)
5. City Projects Listing: manual CSV, email the city, or skip?
6. Contamination data: manual EnviroStor/GeoTracker download, or the dated 2023 snapshot as interim?
7. Phase 2 source PDFs (zoning code chapters + specific plans), saved by Bodie
8. Product name
9. Anthropic API key + spend limit (needed by Phase 4)
10. Airport layer: defer to v2?

## Later TODOs
- LICENSE (MIT, plus a note that data stays under each source's terms): add once the author name is confirmed
- Retry FEMA NFHL from GitHub Actions
- Verify the HE sites inventory (37 Table A sites) against the city's adopted appendix + March 2025 amendment
