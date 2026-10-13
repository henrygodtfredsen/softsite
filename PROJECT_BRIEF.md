# Project Brief: Santa Clara Development Site Screener

> **For Claude Code.** This file is the full spec for a multi-session build. Save it in the repo root as `PROJECT_BRIEF.md` and treat it as the source of truth. Start with Phase 0 and stop at every checkpoint for my approval. Do not write application code until I approve the Phase 0 plan.

---

## 1. Who I am and why this exists

I'm Bodie, an Economics major with a Real Estate minor at Santa Clara University, recruiting for commercial real estate internships (capital markets, development, investment). I'm not a professional software engineer. I've built one web app before with AI-assisted development (a personal investment tracker), so I'm comfortable running commands and reviewing code, but I need you to explain decisions in plain language.

This project is a portfolio piece I will demo live to brokers, developers, and investors, and screen-share on networking calls. It has to look and behave like a real research product, and I have to be able to explain every number and every architectural choice in an interview. **Accuracy and explainability matter more than feature count.**

## 2. What we're building

A web app that screens every parcel in the **City of Santa Clara, CA** for redevelopment potential. It identifies "soft sites", where current zoning allows far more than what is built today. It ranks them with a transparent, adjustable score and layers on live entitlement-pipeline activity. It also generates an AI-written one-page site memo for any parcel and runs a back-of-envelope residual land value analysis.

**The 2-minute demo this must support (build toward this):**
1. The landing page shows headline stats computed from real data, for example parcels analyzed, soft sites identified, total theoretical unit capacity, and the date of the last data refresh.
2. Filter to "El Camino Real Specific Plan" and show the top 10 ranked sites.
3. Click the #1 site. The side panel shows zoning, allowed versus existing intensity, a score breakdown, flags, and nearby pipeline projects.
4. Open its AI site memo. It's a clean, printable one-pager grounded only in the data.
5. Drag the scoring weights (for example, more weight on transit) and watch the rankings re-sort live.
6. Open the feasibility tab, tweak the rent and hard-cost assumptions, and watch residual land value update.
7. Toggle the pipeline layer to show what the Planning Commission has been hearing nearby.

## 3. Working agreement (follow these throughout)

1. **Never fabricate data.** If a source is down, changed, or missing a field, stop and tell me. Do not substitute mock data in anything that ships. Dev fixtures must live in `fixtures/`, be labeled as fake, and never be imported by production code.
2. **Track where every number comes from.** Every figure shown in the UI must trace to a source and a retrieval date. Store raw API responses in `data/raw/<source>/<YYYY-MM-DD>/` and record source URLs in the processed data.
3. **Stop at checkpoints.** At the end of each phase:
   - Summarize what you built and how I can see it (a URL or command).
   - List the decisions you need from me.
   - Wait for my approval before continuing.
4. **Explain as you go.** When you make a non-obvious technical choice, add one or two plain-English sentences to `docs/HOW_IT_WORKS.md` explaining what it is and why.
5. **Keep a log.** Maintain `PROGRESS.md` with what's done, what's next, and open questions. Maintain `CLAUDE.md` with project conventions so future sessions pick up context fast. Read both at the start of every session.
6. **Commit small and often** with clear messages. The repo will be public on GitHub.
7. **Handle secrets and costs carefully.**
   - Keep API keys in `.env.local`. Never commit them.
   - Ask me before adding any paid service, account signup, or anything that costs money.
   - Before using the Anthropic API, estimate the cost.
8. **Be a polite consumer of public data.**
   - Rate-limit requests and cache them.
   - Respect each site's terms of use.
   - Do not scrape the County Assessor's per-parcel lookup site.
9. **Respect privacy.** Never display or store the names of individual (natural-person) property owners. Entity owners such as LLCs and corporations are fine if we have that data. Single-family residential parcels are excluded from rankings by default, with a toggle to include them.
10. **Treat this as a screening tool.** It is not a zoning determination, legal advice, or an appraisal. Say so on the methodology page and in the memo footer.

## 4. Tech stack

These are the defaults. Deviate only with a stated reason, and ask me first if the change is significant.

- **Data pipeline:** Python 3.11+, managed with `uv`. Use `geopandas`/`shapely` for spatial work, `duckdb` (with the spatial extension) for joins and analytics, `httpx` with retry and backoff, and `pydantic` for schemas. Run it as one CLI: `uv run pipeline <step>` or `uv run pipeline all`. Outputs go to `data/processed/` (GeoParquet) and `web/public/data/` (files the web app reads).
- **Web app:** Next.js (App Router) with TypeScript, Tailwind, and shadcn/ui.
  - Maps: MapLibre GL JS via `react-map-gl/maplibre` with a free basemap that needs no API token.
  - Charts: Recharts.
  - Map data: start with simplified GeoJSON. Switch to PMTiles (via tippecanoe) if the parcel file exceeds about 5 MB gzipped or the map feels sluggish.
- **AI:** The Anthropic SDK, using model `claude-sonnet-5-5` (confirm the current model string in Anthropic's docs).
- **Hosting:** Vercel (free tier). The data refresh runs as a weekly GitHub Actions cron that re-runs the pipeline, commits updated data files, and triggers a redeploy.
- **Testing:** `pytest` for pipeline logic (scoring, capacity math, feasibility math), and a light Playwright smoke test that the map loads and a parcel panel opens.
- **Geography is config-driven.** Write the city-specific URLs and field mappings in `config/sources.yaml` so another city (Sunnyvale, San Jose) could be added later without rewriting code.

## 5. Data sources (verified starting points; confirm each in Phase 0)

**Note:** Field names and endpoints below were checked in October 2026, but government services change. Verify them before relying on them.

### City of Santa Clara GIS (ArcGIS REST)
- **Zoning by parcel:** `https://map.santaclaraca.gov/maps/rest/services/OPENDATA/RegionalZoningOpenData/MapServer/0` (layer "Zoning Codes")
  - `ZONGDSGN`: zoning code. It's a coded-value domain that includes the new El Camino Real codes (MUNC, MUCC, MURC, MU-VHD) and the Patrick Henry codes (VHDR, HDF, UV, UC, VR, PH-R5).
  - `SPPLAN`: specific plan area. Codes are SCS = Santa Clara Station, SCB = Stevens Creek, ECR = El Camino Real, DWN = Downtown, FC = Freedom Circle, PH = Patrick Henry Drive, LSAP = Lawrence Station, TE = Tasman East.
  - `HistoricParcelType`: MAP = Mills Act, HR = Historic Resource, PHR = Potentially Historic, PW2 = within 200 ft of a historic property.
  - `FEMAZONE_NOTE`: flood-zone note. Also `ZoningURL` and `GenPlanURL`.
  - `displayField` is APN, but APN may not be in the exposed field list. Confirm how to get APN.
  - `maxRecordCount` is 1000, so paginate with `resultOffset`. Formats are JSON and GeoJSON. Request `outSR=4326`; the native coordinate system is CA State Plane III, in feet.
- **General Plan by parcel:** `https://map.santaclaraca.gov/maps/rest/services/OPENDATA/RegionalGeneralPlanOpenData/MapServer`
- **Parcels, addresses, streets:** `https://map.santaclaraca.gov/maps/rest/services/LAYERS/RegionalBase_Lucity/MapServer` (also `LAYERS/BaseMap/MapServer`). Use these to get parcel polygons with APN and site address if the zoning layer lacks them.
- The `/maps/rest/services/OPENDATA` folder listing blocked an automated fetch for bot detection. Direct service URLs worked. If you hit blocks, set a normal User-Agent, slow down, and tell me.

### Santa Clara County GIS
- **County open-data hub:** `https://maps.santaclaracounty.gov/server/rest/services/opendata/SCCGISHUB/MapServer`
  - Layer 8, "Address Point", has `APN`, house number, street fields, `CITY`, `ZIPCODE`, and `JURISDICTION`. Use it as the APN-to-address crosswalk and for geocoding pipeline projects.
  - `maxRecordCount` is 5000.
- **Assessed values are not free in bulk.** The County Assessor sells data files, including a property-characteristics file and a 2-year condensed sales file with indicated prices. Third-party bulk parcel datasets with assessed land and improvement values also exist for a fee. Do not buy anything. Build the score so it works without assessed values, design an optional `assessor` input that plugs in if I buy the data later, and tell me what it would add.

### Existing buildings (to estimate what's built today)
- **Overture Maps buildings** (free GeoParquet; use the `overturemaps` Python CLI with a bounding box around the city). Some buildings carry `height` and `num_floors`.
- **OpenStreetMap buildings** as a cross-check.
- Estimate existing floor area as footprint area × floors, using a documented default floor count when it's missing. Track a confidence flag per parcel.

### State Housing Element sites inventory (6th cycle, Table A)
- Every California city submits a parcel-level sites inventory to HCD. It includes APN, zoning, minimum and maximum density, existing use, vacancy, and estimated unit capacity by income level.
- Find the current dataset for the City of Santa Clara. It may be HCD's statewide open data or the DGS Affordable Housing Development Opportunities tool. Fall back to the city's adopted Housing Element appendix (Excel or PDF).
- Join it by APN. Note that APN formats vary, so normalize dashes and padding.

### Entitlement pipeline
- **Legistar API (confirmed working):** `https://webapi.legistar.com/v1/santaclara`
  - Body IDs: **Planning Commission = 182**, **City Council and Authorities Concurrent = 138**, **Development Review Hearing = 236**.
  - Pull events, then event items, then matters and attachments (staff reports) for the last 24 months.
- **CEQAnet:** `https://ceqanet.lci.ca.gov`. Pull environmental filings where the City of Santa Clara is lead agency; there's a CSV download. These include notices of preparation (NOPs), EIRs, and exemptions.
  - **Acceptance test:** the July 2026 NOP for the **Network Circle Residential Project (4160–4230 Network Circle, 584 units)** must appear in the pipeline layer, geocoded to the right parcels.
- **City Projects Listing:** `https://www.santaclaraca.gov/business-development/development-projects/projects-listing`. This is a paginated page; parse it politely.
- **Extraction:** Use Claude to turn agenda items and staff-report text into structured records with these fields: project name, address(es), APN(s) if stated, project type, residential units, nonresidential SF, height/stories, entitlement stage, hearing date, decision, source URL.
  - Validate the output against a pydantic schema.
  - Keep the source excerpt for each extracted field so I can audit it.
  - Record `null` rather than guessing.

### Transit and constraints
- **Transit:** VTA GTFS (light rail stops), Caltrain stations (Santa Clara, Lawrence), and the planned BART Santa Clara station if a reliable location is published (label it "planned").
- **Contamination:** DTSC EnviroStor and Water Board GeoTracker site downloads. Flag parcels with or adjacent to open cases.
- **Flood:** use the city's `FEMAZONE_NOTE`, plus the FEMA National Flood Hazard Layer if it's easy to get.
- **Airport (optional):** the San José Mineta airport influence area and height limits from the county's airport land use plan, if available as GIS. North Santa Clara is near the airport, so this matters for height.

### Market context
- **Zillow Research:** ZHVI (home values) and ZORI (rents) by ZIP, as free CSVs. Follow Zillow's attribution terms. Confirm the list of ZIP codes inside the city.
- `data/manual/market_reports.csv`: a small table I fill in by hand from broker quarterly reports (submarket, product type, quarter, asking rent, vacancy, source citation). Do not scrape broker PDFs.

### Context worth knowing (for copy on the methodology page; verify before quoting)
- The updated El Camino Real Specific Plan was adopted in May 2026 with capacity for roughly 4,400 homes.
- The Patrick Henry Drive Specific Plan rezoned about 76 acres of office/industrial land to allow roughly 50–250 homes per acre.

## 6. Build phases and checkpoints

### Phase 0: Recon and plan (no app code)
- Check my environment (Node, Python, `uv`, git, GitHub CLI) and walk me through any installs.
- Hit every source above. Record in `docs/DATA_SOURCES.md`: the URL, fields actually returned, record counts, update cadence, license or terms, and known gaps.
- Propose an exact parcel ID strategy (APN normalization) and the join plan.
- Propose 3 product names.
- List anything that blocks the plan.
- **Checkpoint.**

### Phase 1: Parcel base map (ship a v0)
- The pipeline pulls parcels with zoning, General Plan designation, specific plan, historic status, and flood note. It normalizes to WGS84, computes lot area, and writes processed outputs.
- The web app shows a full-screen map with parcels colored by zoning family and specific plan outlines labeled. Clicking a parcel opens a side panel with its attributes and source links. Add search by address or APN.
- Deploy to Vercel so I have a live URL.
- **Checkpoint.**

### Phase 2: Zoning capacity
- Build `config/zoning_rules.csv` with one row per zoning code. Columns: allowed uses, minimum and maximum density (du/ac), maximum FAR, height limit, notes, and a **citation** (code section or specific plan table with URL).
  - Source it from the city's official zoning code (Title 18) and the adopted specific plans.
  - Mark any row where you're unsure as `needs_review`.
  - I will review this table myself. It's the core real-estate judgment in the project.
- Compute per parcel:
  - theoretical maximum units and maximum gross floor area (GFA)
  - estimated existing GFA and building coverage, from building footprints
  - the capacity gap, in absolute terms and as a ratio
- Join the Housing Element sites inventory.
- Add unit tests for the capacity math.
- **Checkpoint:** show me the 20 parcels with the largest capacity gaps so I can gut-check them.

### Phase 3: Scoring and rankings
Implement the score in Section 7. Then add:
- weight sliders that recompute rankings client-side
- filters for plan area, zoning family, minimum lot size, and excluding flagged or in-pipeline parcels
- a sortable Rankings table with CSV export
- a score-breakdown bar chart in the parcel panel
- URL state, so a link reproduces the exact view (selected parcel, filters, weights)

Add unit tests for scoring. **Checkpoint.**

### Phase 4: Entitlement pipeline layer
- Ingest Legistar, CEQAnet, and the Projects Listing, then extract structured records with Claude.
- Geocode each project via the county address points or the APN; use the Census geocoder as a fallback.
- Deduplicate the same project across sources.
- Map markers styled by stage. Each parcel gets an "In play" label when it's in the pipeline, and a nearby-activity count feeds the score's momentum component.
- Run the Network Circle acceptance test.
- **Validation check.** Temporarily remove the momentum component and see where parcels that later got applications (from the pipeline data) rank on the remaining components. Report the result honestly, even if it's unflattering, and save it to `docs/VALIDATION.md`.
- **Checkpoint.**

### Phase 5: AI site memo
Implement Section 8. Pre-generate memos for the top 50 ranked parcels during the pipeline run and serve them as static files. On-demand generation for other parcels sits behind a per-IP rate limit, a global daily cap, and an environment flag that disables it entirely. Add a printable `/site/[apn]` page with clean typography. **Checkpoint.**

### Phase 6: Feasibility (residual land value)
Add a feasibility tab for the selected parcel, with:
- **Inputs:** product type (podium multifamily, townhomes, office/R&D), average unit size, rent per SF per month, vacancy, operating expense ratio, exit cap rate, hard cost per SF, soft costs as % of hard, impact fees per unit, inclusionary affordable %, and developer return target (margin on cost or target yield on cost; support both).
- **Outputs:**
  - stabilized NOI, stabilized value, and total development cost excluding land
  - residual land value: in total, per buildable unit, and per land SF
  - a comparison against lot size
  - a sensitivity grid, rent ± versus hard cost ±

Show the formulas on screen. **Every default input must either cite a source or be visibly labeled `PLACEHOLDER: needs sourced value`.** Do not invent market numbers; I will supply sourced defaults. **Checkpoint.**

### Phase 7: Market context
Add a Market tab with:
- ZHVI and ZORI time series for the city's ZIPs
- pipeline units proposed per quarter, from Phase 4 data, which shows development momentum over time
- my manual broker-report table, if filled in

**Checkpoint.**

### Phase 8: Polish and ship
- **Landing page:** headline stats, the Top 10 opportunities, last-refreshed date, and an author credit linking to my LinkedIn (I'll supply the link).
- **Methodology page:** scoring, data sources, limitations, and the screening-tool disclaimer.
- **About page.**
- Turn on the GitHub Actions weekly refresh.
- Make it mobile-responsive and run a Lighthouse pass.
- Write the README (Section 10).
- **Final checkpoint.**

## 7. Scoring model (default; all weights live in `config/scoring.yaml`)

The Redevelopment Potential Score runs 0–100: a weighted sum of components, each normalized 0–1 by percentile rank among eligible parcels, minus penalties.

| Component | Default weight | Inputs |
|---|---|---|
| Zoning upside | 35% | Capacity gap (allowed vs. existing, in units for residential-capable zones, GFA otherwise), absolute and ratio |
| Underutilization | 20% | Low building coverage, low estimated existing FAR, large surface-parking share if derivable; building age if assessor data is ever added |
| Site size and shape | 15% | Lot area (sweet spot about 0.5–5 acres; very small lots penalized), compactness |
| Policy tailwinds | 15% | Inside a recently adopted specific plan, on the Housing Element sites inventory, within ½ mile of rail transit |
| Market momentum | 15% | Pipeline projects or units within ½ mile in the last 24 months; ZIP-level rent/price trend |

**Excluded from rankings by default (each one a toggle):**
- public and quasi-public zones (B, PQP, PF, OS)
- single-family zones
- historic resources (HR, PHR, MAP)
- parcels already in the pipeline (labeled "In play" instead)

**Flags, shown in the panel rather than silently removed:**
- contamination case on or adjacent to the parcel
- multiple flood zones
- parcel within 200 ft of a historic property
- low confidence in the existing-building estimate

**Explainability:** for every parcel, store the component scores plus a plain-English "top 3 reasons" list, and show both in the panel.

## 8. AI site memo spec

**Input:** a JSON bundle containing only the facts we hold for that parcel: attributes, capacity math, score breakdown, flags, nearby pipeline records with source URLs, and market context.

**Output:** a one-page memo with these sections:
1. Site Snapshot
2. Zoning and Entitlement Path
3. Redevelopment Thesis
4. Key Risks and Unknowns
5. Nearby Pipeline Activity
6. Next Diligence Steps

**Rules:**
- Use only the facts in the bundle. If something is unknown, say "Not available in public data" and don't guess.
- Every number in the memo must exist in the input bundle. Add a post-generation check that extracts the numbers from the memo and verifies each appears in the bundle, and regenerate or flag on failure.
- Tone: concise and analytical, like a junior analyst's first-pass screen for an acquisitions team.
- Footer: data sources with retrieval dates, plus the screening-tool disclaimer.

Store the prompt in `prompts/site_memo.md` so it's versioned and reviewable.

## 9. UI and design requirements

- **Feel:** an institutional research product, clean and confident, not a hackathon project. Use restrained color, one accent color, and good typography. Offer light and dark basemaps.
- **Layout:**
  - top bar with search, filters, and tabs (Map / Rankings / Pipeline / Market / Methodology)
  - large map
  - right-hand detail panel
  - collapsible weights drawer
- **Map:** color parcels by score with a sequential palette, with an option to switch to zoning or plan area. Outline specific plan boundaries and label them. Show pipeline markers by stage and transit stops and lines. Include a legend.
- **Performance:** first load under about 3 seconds on a laptop. Usable on a phone.
- **Empty and error states:** clear messages instead of blank panels.

## 10. Repo deliverables

- **`README.md`** should cover:
  - the problem and who it's for
  - a demo GIF and screenshots
  - a feature list
  - an architecture diagram (Mermaid)
  - data sources and refresh cadence
  - a methodology summary
  - limitations
  - what I'd build next
  - author
- **`docs/HOW_IT_WORKS.md`:** a plain-English walkthrough of the system, plus a section of 10 likely interview questions about this project with accurate answers based on how it was actually built.
- **Other docs:** `docs/DATA_SOURCES.md`, `docs/VALIDATION.md`, `PROGRESS.md`, `CLAUDE.md`.
- **Repo hygiene:** `.env.example` listing required keys with no values, and a license file (MIT for code; note that data remains under each source's terms).

## 11. Out of scope for v1

- Paid data sources. Design for them, don't buy them.
- User accounts and authentication.
- Cities other than Santa Clara (keep it config-driven so they can be added later).
- State-law overlays such as SB 6, AB 2011, and density bonus. These are a good v2 feature, but eligibility rules are complex. If we add them later, they must show as "potentially eligible – verify" with criteria cited from statute.

## 12. Start here

Read this whole brief. Then begin **Phase 0** and stop at its checkpoint with your findings and plan.
