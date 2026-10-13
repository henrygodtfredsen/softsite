# Progress

## Status: Phase 1 built and verified locally. Next: push to GitHub and deploy to Vercel (walkthrough with Bodie), then the Phase 1 checkpoint (2026-10-13)

## Done

### Phase 0: recon and plan (approved 2026-10-13)
- Every source in the brief was hit live.
  - Findings: `docs/DATA_SOURCES.md`
  - Plan and decisions: `docs/PLAN.md`
- Product name: **SoftSite**.

### Phase 1: parcel base map
- **Project home:** moved to `~/Projects/softsite`, out of iCloud (it broke the Python environment).
- **Pipeline:** `uv run pipeline all`
  - **parcels:** City Land Parcels + Zoning layers, layer-agreement check, multi-part merge, lot area
  - **addresses:** City site addresses → parcel
  - **plan_areas:** derived outlines
  - **export:** files in `web/public/data/`
  - 27 pytest tests pass.
- **Web app (`web/`):** Next.js 16.4 + Tailwind + shadcn/ui + MapLibre 6 on an OpenFreeMap basemap (light/dark).
  - Full-screen map colored by zoning family (3 colorblind-safe groups + neutrals, isolate-a-family legend)
  - Plan-area outlines and labels; "Plan areas" color mode
  - Parcel panel with source links and retrieval dates
  - Address/APN search
  - Mobile bottom sheet
  - Lint, typecheck, and production build pass.
- **Your manual checklist:** `docs/MANUAL_STEPS.md` (Projects Listing pages, Phase 2 PDFs, email draft to Planning).

## Next
1. Create the GitHub repo and push.
2. Connect Vercel (Root Directory = `web`).
3. Phase 1 checkpoint.
4. Phase 2 needs the PDFs in `docs/MANUAL_STEPS.md` §B.

## Open questions for Bodie
- LiDAR vintage flag threshold: you chose `YEARBUILT ≥ 2021`. The flight was in early 2020, so buildings finished during 2020 may also be missing. Keep 2021, or use 2020?

## Later TODOs
- Contamination download instructions (before Phase 3, decision #6)
- Retry FEMA NFHL from GitHub Actions
- Verify the HE sites inventory against the City's adopted appendix + the 2025 amendment
- Old Ironsides TOC rezoning area: no City GIS plan code; handle in Phase 2
- APN 230-05-117: computed 1.659 ac vs published 0.488 ac. Check during Phase 2.
- Mobile: the legend is hidden below 768 px wide; add a legend button
