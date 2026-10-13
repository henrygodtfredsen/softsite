# Data Sources

Phase 0 recon was done on **2026-10-13**. I queried every source below live on that date. Counts are what the service returned that day; they will drift. Query URLs are given so each number can be reproduced.

**Access key**
- ✅ = works for automated pipeline access
- ⚠️ = works, with caveats
- 🚫 = blocked to scripts by bot protection; needs a manual step

All automated requests used the User-Agent `sc-site-screener/0.1 (academic research project)` with a pause of about 1 second between calls.

## Summary

| # | Source | Status | Used for | Refresh |
|---|---|---|---|---|
| 1 | City GIS: Land Parcels (`OPENDATA/RegionalBaseOpenData/7`) | ✅ | **Master parcel layer**: APN, zoning, General Plan, specific plan, historic, year built | Weekly pull |
| 2 | City GIS: Zoning Codes (`OPENDATA/RegionalZoningOpenData/0`) | ✅ | Flood note, code/GP URLs (joins to #1 on OBJECTID) | Weekly pull |
| 3 | City GIS: General Plan (`OPENDATA/RegionalGeneralPlanOpenData/0`) | ✅ | Redundant with #1 (same GP field); kept as a cross-check | — |
| 4 | City GIS: Air Parcels, Site Addresses | ✅ | Condo detection; address search | Weekly pull |
| 5 | County GIS: Address Point (`SCCGISHUB/8`) | ✅ | APN↔address crosswalk; geocoding pipeline projects | Weekly pull |
| 6 | County GIS: LiDAR Building Footprints (`SCCGISHUB/40`) | ✅ | **Existing building area + height** (recommended primary) | Static (2020 flight) |
| 7 | Overture Maps buildings | ✅ | Cross-check; catches post-2020 buildings | Monthly releases |
| 8 | OpenStreetMap (Overpass) | ✅ | Already inside Overture; separate pull not needed | — |
| 9 | State HE sites inventory (DGS/HCD SB 6 map service) | ⚠️ | Housing Element sites (Table A) + rezone sites (Table B) | Weekly pull |
| 10 | Legistar API | ✅ | Hearings, agenda items, staff reports | Weekly pull |
| 11 | CEQAnet CSV | ✅ | NOP/EIR/MND/NOE/NOD filings, City as lead agency | Weekly pull |
| 12 | City Projects Listing | 🚫 | 57 projects with APN, units, file #, status | Manual (see Decisions) |
| 13 | VTA GTFS | ✅ | Light rail stops and lines | Weekly pull |
| 14 | County GIS: Rail Road Stations (`SCCGISHUB/17`) | ✅ | Caltrain/ACE station points | Static |
| 15 | BART Santa Clara (planned) | ⚠️ | No GIS published; manual point with citation | Manual |
| 16 | DTSC EnviroStor | 🚫 | Contamination cases | Manual download |
| 17 | Water Board GeoTracker | 🚫 / ⚠️ | Website blocked; an official GIS copy exists but is a Jan 2023 snapshot | Manual download |
| 18 | FEMA NFHL | ⚠️ | Unreachable from this machine; county layer + city note cover it | — |
| 19 | County GIS: 100-yr Flood (`SCCGISHUB/112`) | ✅ | Flood zone overlay (FEMA DFIRM subset, 2015) | Static |
| 20 | Airport influence area / height (SJC ALUCP) | 🚫 | No public GIS found | Deferred (optional) |
| 21 | Zillow ZHVI / ZORI | ✅ | ZIP-level value and rent trends | Monthly |
| 22 | City zoning code (eCode360) + specific plans | 🚫 | Phase 2 citations | Manual (you save PDFs) |
| 23 | Anthropic API | ✅ (needs key) | Extraction + memos | — |

---

## 1. City of Santa Clara GIS — Land Parcels ✅ (master parcel layer)

**URL:** `https://map.santaclaraca.gov/maps/rest/services/OPENDATA/RegionalBaseOpenData/MapServer/7`

This layer wasn't in the brief, but it's the best one. It already has **APN, zoning, General Plan, specific plan, historic status, acreage, and YEARBUILT** on one polygon per parcel. `maxRecordCount` is **100,000**, so one request returns everything (about 9 MB of attributes, about 3 seconds).

**Fields actually returned**

| Field | Contents |
|---|---|
| `OBJECTID` | ID shared with the zoning layer |
| `APN` | Format `999-99-999` (100% of active land parcels) |
| `PARTYPE` | LND / COM (common area) / ROW / FCE (flood-control easement) |
| `PARCITY` | |
| `PARZIP5` | |
| `TRACTNO` | |
| `APNMAPS` | |
| `GPLANCRT` | General Plan designation (coded domain, 54 values) |
| `ZONGDSGN` | Zoning (coded domain, 97 values) |
| `YEARBUILT` | |
| `ACREAGE` | |
| `CSCVOTEDISTRICT` | |
| `LNDPARSTATUS` | A / R / P (Active / Retired / Pending) |
| `SPPLAN` | Specific plan area |
| `HistoricParcelType` | MAP / HR / PHR / PW2 |

**Counts (2026-10-13)**

| | Count |
|---|---|
| Total features | 29,971 |
| Active (`LNDPARSTATUS='A'`) | 27,736 |
| Active land parcels (`PARTYPE='LND'`) | **27,132** |
| Retired | 2,235 (must be filtered out; they overlap active parcels) |

**Data quality**
- **Duplicate APNs:** 29 among active land parcels (multi-part parcels split into separate features). The pipeline will merge them by APN.
- **`YEARBUILT`:** populated for **98%** of active land parcels (range 1860–2024). Provenance isn't documented in the service; it's probably the county assessor roll passed through the city. I'll label it "per City GIS".
- **`ACREAGE`:** populated for only 54%, so lot area will be computed from geometry instead.
- **Zoning:** null for 12 parcels. General Plan: null for 2.

**ZIP split:** 95051: 13,664 · 95050: 9,213 · 95054: 5,198 · 95053 (SCU): 25 · blank: 1,863.

**Active land parcels by specific plan**

| Plan | Parcels |
|---|---|
| ECR | 458 |
| LSAP | 441 |
| SCS | 143 |
| SCB | 80 |
| DWN | 78 |
| PH | 45 |
| TE | 35 |
| FC | 17 |
| (none) | 25,835 |

**Top zoning codes (active land parcels)**

| Code | Parcels |
|---|---|
| R1-6L | 15,743 |
| PD | 4,411 |
| PD-MC | 1,686 |
| R3 | 1,673 |
| R2 | 749 |
| LSAP | 441 |
| R1-8L | 436 |
| LI | 342 |
| LO-RD | 338 |
| MUCC | 273 |
| HI | 206 |
| PQP | 173 |
| CR | 108 |
| HO-RD | 97 |
| MUNC | 88 |
| DNTW | 77 |
| MURC | 40 |

The ECR codes from the brief (MUNC, MUCC, MURC) and the Patrick Henry codes (VHDR, HDF, UV, UC, VR, PH-R5) are present.

> ⚠️ **Real-estate note:** about **22% of active parcels (6,097) are zoned PD or PD-MC** (Planned Development). PD has no fixed density in the zoning code; each PD's approved plan governs. The General Plan designation is the best available proxy for allowed density (see `docs/PLAN.md`).

**Other details**
- **Coordinate system:** native is NAD83(2011) California State Plane Zone III, US feet (WKID 103005 / EPSG **6420**). The service will reproject to `outSR=4326` on request.
- **⚠️ Bot protection:** the server sits behind Cloudflare. A query with `where=... AND YEARBUILT IS NULL` was **blocked** as a suspected SQL injection; simple `where` clauses worked. The pipeline will always pull `where=1=1` and filter locally.
- **License/terms:** no license text in the service metadata; the service copyright is "City of Santa Clara". The data is published in the city's `OPENDATA` folder for public use. Attribute it as "City of Santa Clara GIS". The city's website is blocked to scripts (see #12), so I couldn't read a portal-level disclaimer.
- **Update cadence:** not stated. Parcel/zoning edits happen as the city processes rezonings, so a weekly pull is ample.

**Reproduce**

```
.../MapServer/7/query?where=1%3D1&returnCountOnly=true&f=json        → {"count":29971}
.../MapServer/7/query?where=1%3D1&outFields=*&returnGeometry=false&f=json   (all attributes)
```

**Map size estimate:** 2,000 features as GeoJSON (4 properties, 6-decimal coordinates) are 0.73 MB raw / 0.09 MB gzipped. Extrapolated to 27.7k parcels, that's about **10 MB raw / 1.3 MB gzipped**, well under the brief's 5 MB-gzipped PMTiles threshold. GeoJSON is fine for v0.

## 2. City GIS — Zoning Codes ✅

**URL:** `https://map.santaclaraca.gov/maps/rest/services/OPENDATA/RegionalZoningOpenData/MapServer/0`

**APN is NOT exposed.** The brief suspected this: `displayField` is APN, but `outFields=APN` returns HTTP 400. It turns out to be the same underlying parcel feature class as #1:
- the same 29,971 features
- the same OBJECTIDs (spot-checked: OBJECTID 19 is MUCC/ECR in both, APN 220-31-079)

This layer adds four fields that #1 lacks:

| Field | Values (count) |
|---|---|
| `FEMAZONE_NOTE` | `MULTI` 951, `LOMA` 1, null 29,019 |
| `ZoningURL` | link to the code chapter |
| `GenPlanURL` | link to the GP land-use page |

Its `HistoricParcelType` counts (all features, active and retired): PHR 1,639 · PW2 1,412 · HR 255 · MAP 133.

**Join to #1:** on `OBJECTID`, with a geometry-equality check asserted in the pipeline.

`maxRecordCount` is 1,000, so pull with `resultOffset` paging (30 requests).

> ⚠️ **Stale links:** `ZoningURL` values point to `codepublishing.com`. That site now redirects to **eCode360** (`https://ecode360.com/SA4626`), so these links are stale and citations should use eCode360.

**OPENDATA folder listing:** this worked for me with the UA above. It lists four services: `CSCAddress_Active`, `RegionalBaseOpenData`, `RegionalGeneralPlanOpenData`, `RegionalZoningOpenData`.

## 3. City GIS — General Plan ✅ (redundant)

**URL:** `.../OPENDATA/RegionalGeneralPlanOpenData/MapServer/0`

This has the same `GPLANCRT` field and domain as #1. There's no need to pull it separately; it's kept as a cross-check.

## 4. City GIS — Air Parcels, Site Addresses ✅

- **Air Parcels** (`RegionalBaseOpenData/6`): **3,006** features. These are condo units stacked over land parcels. A land parcel with air parcels on it has fractured ownership and is very hard to assemble, so it gets a flag.
- **Site Addresses** (`RegionalBaseOpenData/2`): **34,683** points. Fields:
  - `FULLADDR`, `ADDRNUM`, `FULLNAME`, `SITEADUN`, `MUNICIPALITY`, `STADZIP5`
  - lat/long
  - no APN, so APN comes via spatial join or the county crosswalk
- The **`LAYERS/RegionalBase_Lucity`** and **`LAYERS/BaseMap`** services named in the brief also work. They're the same layers at `maxRecordCount` 1,000, so `OPENDATA` is preferred.
- **`OPENDATA/CSCAddress_Active`** exposes `MAILING1` / `MAILING2` fields. I'm **not ingesting this layer** because it may hold mailing-address information we don't need (privacy rule #9).

## 5. County GIS — Address Point ✅

**URL:** `https://maps.santaclaracounty.gov/server/rest/services/opendata/SCCGISHUB/MapServer/8`

**Fields**
- `APN` — **8 digits, no dashes**, e.g. `09708058`
- `HOUSENUMTEXT`, `UNITNUMBER`, `STREETPREFIX`, `STREETNAME`, `STREETTYPE`, `STREETSUFFIX`
- `CITY`, `ZIPCODE`, `JURISDICTION`
- `SOURCE`, `CREATEDDATE`, `MODIFIEDDATE`
- Also returned: `POINT_ID`, `COMMADDR_DISP`, `ADDR_FLAG`, `FLOOR`, `COMM_ANNOTEXT`

**Count:** `CITY='SANTA CLARA'` → **32,391** points. `maxRecordCount` 5,000.

**Terms:** each layer description carries the county's standard "PROVIDED AS IS… NO WARRANTIES" disclaimer. Attribute it as "County of Santa Clara".

**Acceptance-test check:** Network Circle addresses 4160–4220 all map to APN **097-08-058**. 4110–4140 map to 097-08-114. There's no 4230 point in the county data.

The same hub has other useful layers: Parcels (116, FY2025 with situs address), Air Polygon (100), Census tracts/blocks, ZCTAs, and Alquist-Priolo fault zones (101). These are available if needed.

## 6. County GIS — LiDAR Building Footprints ✅ (recommended primary for existing buildings)

**URL:** `.../SCCGISHUB/MapServer/40` ("Buildings Footprints 2D")

This is a better source than the brief anticipated. Footprints were derived from a **county-wide LiDAR flight in early 2020** (Sanborn Map Co.; USGS Base Lidar Spec v2.1).

**Every building has a measured height:**

| Field | Meaning |
|---|---|
| `Building_H` | Building height, feet (sample average 16 ft, max 190 ft in the city bbox) |
| `Base_Heigh` | Ground elevation, feet NAVD88 |
| `Shape_Area_StatePlane` | Footprint area, sq ft |

**Count:** **54,149** footprints in the bbox (-122.00, 37.32, -121.92, 37.42), which includes slivers of neighboring cities.

**Gap:** buildings built or demolished after early 2020 are wrong or missing. Mitigation:
- cross-check against Overture (#7) and the parcel `YEARBUILT` (#1)
- flag parcels with `YEARBUILT ≥ 2020` as lower confidence

**Copyright:** "County of Santa Clara; Sanborn Map Co." under the standard AS-IS disclaimer.

## 7. Overture Maps buildings ✅ (cross-check)

**How:** `uvx overturemaps download --bbox=... -f geoparquet --type=building`. The CLI works; the release on 2026-10-13 is **2026-09-23.1**.

**Sample:** bbox -121.99, 37.348, -121.97, 37.36 (around El Camino near Lawrence) returned **3,334 buildings**.

| Field | Coverage |
|---|---|
| `height` | 74% (from USGS LiDAR) |
| `num_floors` | **0.3%** (11 buildings) |
| `class` | 6% |
| `subtype` | 7% |

Source mix: OpenStreetMap 3,308, USGS Lidar 2,190, Microsoft ML 289.

**Conclusion:** `num_floors` is effectively absent, and Overture's heights largely come from LiDAR anyway. The county layer (#6) is more complete, so Overture is a cross-check and a way to catch post-2020 buildings.

**License:** Overture's buildings theme is **ODbL** because it's OSM-derived. Attribute "© OpenStreetMap contributors, Overture Maps Foundation". If we publish a derived database built *from* Overture footprints, ODbL share-alike applies to that derived database. That's another reason to use county footprints as the primary.

## 8. OpenStreetMap ✅ (no separate pull needed)

An Overpass count over the same sample bbox returned **3,290** building ways (OSM base 2026-10-13). That's almost the same as Overture's 3,334, because Overture's buildings *are* mostly OSM. A separate OSM pull would duplicate #7, so I recommend dropping it.

## 9. Housing Element Sites Inventory (6th cycle) ⚠️

**HCD itself publishes no statewide sites download.** The state's public copy is the **DGS "Housing and Local Land Development Opportunities" map** (SB 6 / AB 1255). Its app's data services are public ArcGIS Feature Services:

| Table | Service | Santa Clara records | Total capacity |
|---|---|---|---|
| Table A (sites) | `https://services8.arcgis.com/a4GMqC2tQHvYiVtK/arcgis/rest/services/SB6_ParcelsA_Pub_Join/FeatureServer/4` | **37** (`jurisdiction_name='SANTA CLARA'`) | **7,821 units** |
| Table B (rezone sites) | `.../Housing_Element__SB6B__ply_join/FeatureServer/4` | **15** | **805 units** |

**Fields**
- `AssessorParcelNumber` (`999-99-999`)
- `fips_apn` (`06085_10404131`)
- `Site_Address_Intersection`
- `Zoning_Designation_Current`
- `Min_Density`, `Max_Density` — **null for all Santa Clara rows**
- `Parcel_Size_Acres`
- `Existing_Use_Vacancy`, `Site_Status` (Available 30 / Pending Project 7)
- `Lower_Income_Capacity`, `Moderate_Income_Capacity`, `Above_Moderate_Income_Capacity`, `Total_Capacity`
- `Latitude`, `Longitude`

Santa Clara's Table A zoning mix: TN 16, UV 7, LSAP 4, HDF 4, VHDMU 2, PD-MC 2, VHDR 1, UC 1. **Layer last edited 2026-10-07.**

**Gap / open question:** 37 sites looks small against the City's RHNA of 11,632 units. That's plausible, because the City leaned on ~12,000 already-approved pipeline units (per [San José Spotlight](https://sanjosespotlight.com/santa-clara-one-step-closer-to-state-housing-approval/)), which don't appear in Table A. The Planning Commission also heard a **March 2025 amendment to the sites list**, and I can't confirm the DGS copy reflects it. To verify, compare against the City's adopted Housing Element sites appendix. That's on santaclaraca.gov, which is blocked to scripts (see Decisions).

**Terms:** state public data; no license stated on the services. Attribute "CA HCD / DGS Housing Element Sites (SB 6)".

## 10. Legistar API ✅

**URL:** `https://webapi.legistar.com/v1/santaclara`. No key needed; no published rate limit (we'll stay ≤1 req/s and cache).

**Body IDs confirmed:**
- **182** Planning Commission
- **138** City Council and Authorities Concurrent
- **236** Development Review Hearing

All active. 54 bodies total.

**Events since 2024-10-01:** PC **25** · DRH **26** · Council (138) **82**.

**Event items** (`/events/{id}/eventitems?Attachments=1`) return:
- full item titles
- matter ID and file number
- `EventItemActionName`, `EventItemPassedFlagName`
- attachments with direct URLs (PDF / DOC / DOCX; e.g. "Project Data & Compliance", "Conditions of Approval", "Vicinity Map", resolutions)

**PC + DRH matters, last 24 months:** **275** distinct. 182 of them look land-use-related (keyword match), with **1,057 attachments** on those. Many DRH items are single-family additions, which a title pre-filter will drop before any AI extraction.

Example title: *"Recommendation on a Prezone… and Vesting Tentative Subdivision Map to Allow the Development of 408 residential units… at 451–475 El Camino Real"* (file 26-900, PC 2026-09-02, Adopted).

**Notes**
- The same matter repeats across several event items (one per motion), so dedupe on `EventItemMatterId`.
- Council events returned `EventAgendaFile: null` at the event level. Items still need checking in Phase 4.
- **Network Circle is not on any PC/DRH agenda yet.** That's expected: it's at the NOP stage.

## 11. CEQAnet ✅

**CSV:** `https://ceqanet.lci.ca.gov/Search?LeadAgency=Santa+Clara%2C+City+of&StartRange=2024-10-01&EndRange=2026-10-13&OutputFormat=CSV`

`robots.txt` allows `/` and disallows only `/*/AttachmentZip`.

**Rows:** **52** documents (2024-10-01 → 2026-10-13): NOD 28 · NOP 7 · NOE 6 · MND 5 · EIR 3 · FIN 2 · SIR 1.

**Columns (55)**
- SCH Number, Document Type, Received, Document Title, Document Description, Document Portal URL
- **Location Coordinates** (DMS text; the degree sign is missing in the CSV, e.g. `3723'32.55"N 12157'9.21"W`)
- Location Cross Streets, **Location Parcel Number** (free text, e.g. `APNs 097-01-073, -039; 104-01-102`)
- Location Total Acres
- NOC Development Type (e.g. `Residential (Units 584, Acres 38)`), NOC Local Action
- NOD approval fields
- Contact name / email / phone — **we will drop these columns**

> ✅ **Acceptance test record found:** SCH **2026070438**, NOP received **7/13/2026**, "Network Circle Residential Project"
> - **584 units:** 120 affordable apartments, 416 townhomes, 48 single-family homes
> - **APN 097-08-058**, 38 acres
> - Location: Lafayette St & Network Circle
> - Current GP is High Intensity Office/R&D; zoning is PD
> - Filed under Gov. Code §65589.5(d)(5) (the "builder's remedy" provision of the Housing Accountability Act)
>
> The city parcel 097-08-058 is **58.2 acres**, PD / HDRD. The project site (38 ac) is a portion of it; the remainder includes Agnews Historic Park.

## 12. City Projects Listing 🚫

**URL:** `https://www.santaclaraca.gov/business-development/development-projects/projects-listing`

**Blocked for scripts.** Akamai returns **HTTP 403** for:
- our UA
- a normal browser UA
- WebFetch
- even `robots.txt`

I didn't attempt further workarounds, since bypassing bot protection would break the working agreement.

In a real browser the page loads: **57 projects**, 10 per page, filterable by Approved / Completed / Pending Review / Under Construction. Each detail page (e.g. `/Home/Components/BusinessDirectory/BusinessDirectory/678/2495`) shows:
- Project Description (with unit counts)
- Total Site Area, Density
- **File Number** (PLN…), **Parcel Number**
- Applicant/Owner (entities, e.g. "City Ventures")
- Project Planner, Current Status

This is high-value, low-volume data. See the Decisions section of `docs/PLAN.md` for options.

## 13. VTA GTFS ✅

**URL:** `https://gtfs.vta.org/gtfs_vta.zip`. 4.7 MB, `Last-Modified` 2026-08-31.

- **Feed:** valid 2026-08-10 → 2026-10-25 (`feed_version` 2026-08-27_10:32). It's republished each service change, so the weekly pull picks up new versions.
- **Light rail routes:** Blue, Green, and Orange lines, plus event variants.
- **Light rail stations in the city bbox (15):**
  - Great America, Lick Mill, Champion, Old Ironsides, Reamwood, Vienna, Tasman
  - Bonaventura, Orchard, River Oaks, Karina, Component, Cisco, Baypointe
  - Patrick Henry Pocket Track (**not a public stop**, so excluded)
- Distances are computed from parcels, so stations just outside the city line still count.
- **Terms:** VTA's developer page offers the feed for public apps with no key. Attribute "VTA".

## 14. County GIS — Rail Road Stations ✅ (Caltrain)

**URL:** `.../SCCGISHUB/MapServer/17`

In and near the city:
- **Santa Clara Station** (37.35291, -121.93659)
- **Lawrence Station** (37.37094, -121.99690)
- **Great America Station** (37.40658, -121.96700; ACE / Capitol Corridor)
- College Park (San José)

The layer was last updated in 2012. Stations don't move, so that's fine for location.

## 15. BART Santa Clara Station (planned) ⚠️

I found no GIS point. VTA's BART Silicon Valley fact sheet places the station **"adjacent to the Santa Clara Transit Center and Gateway Crossings development at Brokaw Road and future Champions Way"** ([VTA fact sheet](https://vtabart.org/wp-content/uploads/2026/08/VTABSV_FactSheet_2025_SantaClara_01062026-2.pdf)).

The opening date is reported inconsistently: 2029–2030 in local press, and later in a 2024 CEQA addendum. **Plan:** place one manual point with that citation, labeled **"Planned – opening date not confirmed"**. Don't count it as existing transit in the default score (toggle).

## 16. DTSC EnviroStor 🚫

`https://www.envirostor.dtsc.ca.gov/public/data_download` returns a **Cloudflare challenge**: 403 for scripts, and "Performing security verification" even in the built-in browser. I did not try to get past it.

A person in a normal browser can use the site's "Data Download" exports. **Manual step** (see Decisions).

## 17. Water Board GeoTracker 🚫 / ⚠️

The `geotracker.waterboards.ca.gov/data_download_by_county` page has the same Cloudflare challenge.

**Alternative found:** the Water Board's own public ArcGIS service `https://gispublic.waterboards.ca.gov/portalserver/rest/services/Hosted/geotracker_sites_download/FeatureServer/371`.
- Its item summary says **"Sites tracked in GeoTracker downloaded on Jan 2, 2023"**, and the latest `status_dat` is 2022-12-21, so it's **~3.8 years stale**.
- In the city bbox: **615 sites**. 475 are "Completed – Case Closed"; about **100 are open** (various "Open – …" statuses).
- Fields include `business_n`, address, lat/long, `case_type`, `status`, `status_dat`, and `site_histo`.

Usable as a clearly dated interim layer.

## 18. FEMA National Flood Hazard Layer ⚠️

`hazards.fema.gov/.../NFHL/MapServer` reset the connection from this machine. I tried two URL forms over IPv4. FEMA's GIS endpoints are known to refuse some networks, so it may work from GitHub Actions (US-hosted runners); I'll retry there.

Not needed for v1, since #19 plus the city's `FEMAZONE_NOTE` cover the brief's "multiple flood zones" flag.

## 19. County GIS — 100-Year Flood Hazard Zones ✅

**URL:** `.../SCCGISHUB/MapServer/112`. A subset of FEMA DFIRM, publication date 2015. Field: `Flood_Zone`. One (dissolved) feature intersects the city bbox.

## 20. Airport influence area / height limits (SJC) 🚫 (optional)

The County ALUC's SJC Comprehensive Land Use Plan and its 2024 AIA amendment (CEQAnet [2024020273](https://ceqanet.lci.ca.gov/2024020273)) exist as PDFs, but **I found no public GIS layer** for the Airport Influence Area or the FAA Part 77 surfaces. The county hub has only "Airports Outline" (29), which is runway linework. I recommend deferring this to v2, or emailing the County ALUC for the shapefile.

## 21. Zillow Research ✅

| File | Size | Last-Modified |
|---|---|---|
| ZHVI by ZIP — `https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | 124 MB | 2026-09-16 |
| ZORI by ZIP — `https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv` | 10 MB | 2026-09-16 |

ZORI's latest month is **2026-08-31**, and it has rows for **95050, 95051, 95054**. There's no 95053 row (that ZIP is the SCU campus, 25 parcels).

**City ZIPs** (from parcel `PARZIP5`): 95050, 95051, 95054, plus 95053 (SCU). Stray 95110/95134 values (8 parcels) are edge cases.

Updated monthly per Zillow's data page. Zillow's page links its Terms of Use and a "ZHVI User Guide" for citation. I'll copy the exact attribution wording into the Market tab in Phase 7. I couldn't fetch Zillow's pages by script (403), so I'll verify the wording then.

## 22. City zoning code (Title 18) and specific plans 🚫

The code moved from codepublishing.com to **eCode360** (`https://ecode360.com/SA4626`), which is behind a Cloudflare challenge. The adopted specific plans are on santaclaraca.gov (Akamai, blocked; see #12). Phase 2 needs these documents for every citation in `config/zoning_rules.csv`. See Decisions.

## 23. Anthropic API ✅

The model ID **`claude-sonnet-5-5`** is confirmed current (Anthropic model table cached 2026-10-06).

| | Price |
|---|---|
| Input | $2 / M tokens |
| Output | $10 / M tokens |
| Cache reads | $0.20 / M tokens |
| Batch API | 50% off |

Cost estimate is in `docs/PLAN.md`. Needs an API key from you before Phase 4.

---

## Context facts for the methodology page (verified 2026-10-13)

- **El Camino Real Specific Plan:** adopted by City Council in **May 2026** (unanimous), with capacity for **~4,400 homes**, up to 6 stories and up to 100 du/ac in parts; plan area about 250 acres. Source: [SV@Home, May 28 2026](https://siliconvalleyathome.org/santa-clara-takes-a-big-step-forward-on-el-camino-real-housing/). ✅ matches the brief.
- **Patrick Henry Drive Specific Plan:** adopted **March 22, 2022**. The brief's "about 76 acres" comes from the 2019 environmental notice; the **adopted plan says ~73.6 acres**, and the city page says ~74. Densities of **50–250 du/ac** are per [San José Spotlight](https://sanjosespotlight.com/santa-clara-76-acres-rezoning-could-add-thousands-of-homes); capacity is up to 12,000 homes. ⚠️ Use "about 74 acres" and cite the adopted plan once we have it.
- **RHNA 2023–2031:** 11,632 units (2,872 VLI / 1,653 LI / 1,981 Mod / 5,126 Above-Mod).
