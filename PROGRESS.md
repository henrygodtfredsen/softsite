# Progress

## Status: Phase 1 approved (2026-10-13) and live at https://softsite-sepia.vercel.app. Phase 2 is waiting on Bodie's source-document downloads.

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

- **Live site:** https://softsite-sepia.vercel.app
  - Vercel Hobby, Root Directory `web`; every push to `main` redeploys.
  - Verified 2026-10-13: all data files 200 (Brotli-compressed), no console errors, search → panel works.
- **Repo:** https://github.com/henrygodtfredsen/softsite (public).

## Next
1. Phase 1 approved 2026-10-13. Public name: Henry Godtfredsen. LiDAR flag threshold: 2020.
2. Phase 2 (zoning capacity) needs Bodie's downloads from `docs/MANUAL_STEPS.md`, Part 1.

## Open questions for Bodie
- None right now.

## Later TODOs
- Contamination download instructions (before Phase 3, decision #6)
- Retry FEMA NFHL from GitHub Actions
- Verify the HE sites inventory against the City's adopted appendix + the 2025 amendment
- Old Ironsides TOC rezoning area: no City GIS plan code; handle in Phase 2
- APN 230-05-117: computed 1.659 ac vs published 0.488 ac. Check during Phase 2.
- Mobile: the legend is hidden below 768 px wide; add a legend button
