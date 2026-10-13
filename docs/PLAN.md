# SoftSite — Plan

- Phase 0 recon: 2026-10-13. Facts behind this plan are in `docs/DATA_SOURCES.md`.
- **Phase 0 approved by Bodie on 2026-10-13** with the decisions below. Where a section says "Decision", it's settled. Change it only with Bodie's OK.

## Decisions log (Phase 0 checkpoint, 2026-10-13)

| # | Topic | Decision |
|---|---|---|
| 1 | Git identity | Bodie's GitHub no-reply email |
| 2 | Accounts | GitHub CLI + free Vercel (Hobby) account, signed up via GitHub. Walk Bodie through connecting the repo at deploy time. |
| 3 | PD parcels | General Plan density as the stand-in, with the rules in §4 |
| 4 | Existing buildings | County LiDAR primary, Overture cross-check, no separate OSM pull. Floor-count rules in §3. |
| 5 | City Projects Listing | Bodie saves the pages from his browser into `data/manual/projects_listing/`; the pipeline parses them locally. Claude drafts an email to Planning asking for a data export; Bodie sends it. |
| 6 | Contamination | The Jan 2023 Water Board GeoTracker copy is a **development placeholder only**. Before Phase 3, Claude gives Bodie the exact download pages and file names; he downloads current GeoTracker + EnviroStor files. Every contamination flag shows its data date. |
| 7 | Phase 2 documents | Claude provides a checklist with URLs and file names (in `docs/MANUAL_STEPS.md`), including the City's adopted Housing Element sites appendix, to check the state's 37-site / 7,821-unit copy. |
| 8 | Product name | **SoftSite** |
| 9 | Anthropic API | Bodie creates a key with a monthly spend limit before Phase 4. **On-demand memo generation is OFF in production at launch**; only pre-generated memos are served. |
| 10 | Airport height limits | Deferred to v2. Methodology notes that capacity near SJC may be overstated. |
| 11 | Building age | Add to the Underutilization component (older → higher). See `config/scoring.yaml`. |
| 12 | Flood | City `FEMAZONE_NOTE` + county 100-yr flood layer instead of FEMA NFHL |

## 1. Parcel ID strategy (APN normalization)

**The canonical key is `apn`: an 8-character string of digits, e.g. `09708058`.**

| Source | Raw form | Rule |
|---|---|---|
| City GIS (`APN`) | `097-08-058` | strip non-digits |
| County address points (`APN`) | `09708058` | as-is |
| DGS/HCD sites (`AssessorParcelNumber`, `fips_apn`) | `097-08-058`, `06085_09708058` | strip `06085_` prefix, then non-digits |
| CEQAnet (`Location Parcel Number`) | free text: `APNs 097-01-073, -039; 104-01-102` | parse a list; a short form like `-039` inherits the book-page (`097-01`) from the previous APN |
| Legistar / staff reports / Projects Listing | `230-05-021` in prose | regex `\b\d{3}-\d{2}-\d{3}\b`, then strip |
| Excel-sourced files | `9708058` (leading zero lost) | left-pad to 8 when the result is 7 digits |

`normalize_apn(raw) -> str | None` returns `None` for anything that isn't 8 digits after cleaning. It never guesses. Unmatched values are logged to `data/processed/unmatched_apns.csv` with their source. The display format is `097-08-058`.

**Parcel universe:**
- **Mapped:** City Land Parcels with `LNDPARSTATUS = 'A'`, dissolved by APN.
- **Ranked (from Phase 3):** only `PARTYPE = 'LND'` (27,132 parcels).
- **Context only:** `COM` (condo common areas), `ROW` (right-of-way), and `FCE` (flood-control easements) are mapped but never ranked.
- **Dropped:** retired parcels.

## 2. Join plan

```
City Land Parcels (layer 7) ──OBJECTID──▶ City Zoning layer (FEMAZONE_NOTE, URLs)
   │  (assert ZONGDSGN/SPPLAN/status agree on every OBJECTID)
   ├─ spatial ──▶ City Site Addresses    → address search (point-in-parcel)
   ├─ spatial ──▶ City Air Parcels       → "condominium / fractured ownership" flag
   ├─ spatial ──▶ County LiDAR footprints → existing GFA, coverage, height
   ├─ spatial ──▶ Overture buildings     → cross-check + post-2020 buildings
   ├─ apn ──────▶ HCD/DGS sites (Table A/B) → on Housing Element list, HE capacity
   ├─ distance ─▶ VTA LRT stops, Caltrain/ACE stations (+ planned BART, toggle)
   ├─ spatial ──▶ County 100-yr flood zone, GeoTracker/EnviroStor points (buffer)
   └─ pipeline ─▶ project records → "In play", nearby activity
```

**Pipeline project → parcel**, in order of confidence (the method used is stored on each record):
1. APN stated in the source
2. Address → county address points → APN
3. CEQAnet coordinates → point-in-parcel
4. Census geocoder → point-in-parcel (low confidence)

**Geometry:**
- Areas and distances are computed in **EPSG:6420** (CA State Plane III, US ft).
- The map is served in **WGS84** (EPSG:4326).

## 3. Existing-building estimate — Decision (with Bodie's adjustments)

```
footprint_area = Σ (area of each county LiDAR footprint ∩ parcel)       [sq ft]
floors_i       = max(1, floor(height_i / floor_to_floor(zone family)))
existing_GFA   = Σ (footprint_area_i × floors_i)
coverage       = footprint_area / lot_area
existing_FAR   = existing_GFA / lot_area
```

| Zone family (from the parcel's zoning, or GP for PD) | `floor_to_floor` |
|---|---|
| Residential | 12 ft |
| Office / R&D, commercial, mixed use | 15 ft |
| Industrial | 24 ft (so a 30 ft single-story warehouse counts as 1 floor) |

- **Minimum 1 floor** per building.
- **Roof-height measure:** if a source offers more than one height measure, use the median or mean roof height, never the maximum, so rooftop equipment and parapets don't add floors.
  - ⚠️ The county layer has only **one** height field (`Building_H`), and its metadata doesn't say whether it is the max, median, or mean of the LiDAR returns.
  - The calibration below will reveal any bias.
  - Overture's `height` (where present) is the second measure for comparison.
- **Calibration (Phase 2):** about 20 buildings with known story counts, including:
  - a warehouse
  - a two-story R&D building
  - a data center
  - garden apartments
  - a mid-rise
  - a podium project
  - single-family homes

  I'll report the error rate in `docs/VALIDATION.md`.
- **LiDAR vintage flag:** parcels with `YEARBUILT ≥ 2020` are flagged "building may be missing or wrong in 2020 LiDAR". The threshold lives in config.
  - Bodie proposed 2021; at the Phase 1 checkpoint he left the call to Claude.
  - 2020 was chosen because 386 parcels report `YEARBUILT` 2020, all non-single-family projects likely under construction during the early-2020 flight. That's more than the 162 built in 2021 or later.

**Confidence flag per parcel:**

| Confidence | When |
|---|---|
| high | year built before the threshold **and** county vs. Overture footprint area within ±25% |
| medium | either condition fails |
| low | year built ≥ threshold, **or** no footprint on a parcel that has a `YEARBUILT` |

## 4. Planned Development (PD) zoning — Decision

6,097 active parcels (22%) are PD / PD-MC. For them:

- **Proxy:** use the **General Plan designation's density/FAR** as the allowed intensity.
- **`density_basis`:** every parcel stores `density_basis` = `"zoning"` or `"general_plan_pd_proxy"`, and the parcel panel shows it.
- **Upper bound:** PD capacity is treated as an **upper bound** and marked **lower confidence**.
- **Filter:** a toggle **excludes PD parcels from rankings**.
- **Methodology note:** projects filed under the **builder's remedy** (Gov. Code §65589.5(d)(5)), such as Network Circle, can exceed both zoning and the General Plan. The screener can't predict their capacity; they appear through the pipeline layer as **"In play"**.

`config/zoning_rules.csv` (Phase 2) will therefore have rows for General Plan designations as well as zoning codes.

## 5. Score inputs

- **Building age** (from City `YEARBUILT`, 98% coverage) is added to **Underutilization**: older buildings score higher. The default sub-weight is in `config/scoring.yaml`; Phase 3 implements it.
- **What the paid assessor file would add later:**
  - improvement-to-land value ratio (the classic soft-site test)
  - last sale date/price
  - use codes

  The `assessor` input will be an optional join on `apn`.

## 6. Anthropic API cost estimate

**Model:** `claude-sonnet-5-5` ($2 in / $10 out per M tokens; Batch API 50% off; cache reads $0.20/M).

| Item | Estimate |
|---|---|
| Extraction backfill (≈450 agenda titles, ≈80 staff reports, 52 CEQAnet records) | ~$13 (~$7 with Batch API) |
| Weekly extraction increment | < $0.50 |
| 50 pre-generated memos, incl. ~30% number-check retries | ~$4 per full run |
| Weekly memo regeneration (only changed bundles) | $0–4 |
| On-demand memos | **off at launch** (Decision 9) |

**Total:** about **$20 one-time**, then about **$5–15/month**. Every call logs `usage`.

## 7. Product name — Decision: **SoftSite**

## 8. Blockers (as of Phase 1 start)

| Blocker | Blocks | Owner |
|---|---|---|
| `gh auth login` + git identity | Commits / GitHub push | Bodie (in progress) |
| Vercel Hobby account | Phase 1 live URL | Bodie, walked through at deploy |
| Zoning code + specific plans + HE appendix PDFs | Phase 2 citations | Bodie, checklist in `docs/MANUAL_STEPS.md` |
| Projects Listing pages | Part of Phase 4 | Bodie, checklist in `docs/MANUAL_STEPS.md` |
| Current EnviroStor / GeoTracker files | Contamination flags (Phase 3) | Bodie; Claude provides download steps before Phase 3 |
| Anthropic API key | Phase 4–5 | Bodie |

**Weekly-refresh caveat:** manually sourced layers don't auto-refresh. The UI shows each source's own "as of" date.

## 9. Repo layout

```
config/            sources.yaml, zoning_families.csv, zoning_rules.csv (Ph 2), scoring.yaml
pipeline/          Python package (uv) → `uv run pipeline <step>`
data/raw/          raw API responses by source/date   (gitignored)
data/manual/       hand-maintained inputs (committed); source_docs/ PDFs (gitignored)
data/processed/    GeoParquet outputs                  (gitignored)
web/               Next.js app; web/public/data/ = files the app reads (committed)
prompts/           site_memo.md, extraction prompts
fixtures/          labeled fake data for tests only
docs/              DATA_SOURCES, PLAN, METHODOLOGY, MANUAL_STEPS, HOW_IT_WORKS, VALIDATION
```
