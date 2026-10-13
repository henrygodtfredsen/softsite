# Manual steps for Bodie

Some public sources block automated downloads (see `docs/DATA_SOURCES.md`). For those, you save the files from your own browser and the pipeline reads them from `data/manual/`. This file lists exactly what to save, where, and under what name.

**General rules**
- **Web pages:** in Chrome, use File → Save Page As… → Format: **"Webpage, HTML Only"**.
- **PDFs:** use the site's download link. Name them as shown so the pipeline can find them.
- **Data dates:** put the date you saved things in the folder name (`YYYY-MM-DD`). That date becomes the data's "retrieved" date in the app.
- **What gets committed:** source PDFs and saved HTML pages are **not** committed (they're gitignored). Only the structured data the pipeline extracts from them is committed, with citations back to the originals.

---

## A. City Projects Listing (needed for Phase 4)

**Folder:** `data/manual/projects_listing/<YYYY-MM-DD>/`

**1. The 6 listing pages** (10 projects each, 57 projects as of 2026-10-13). Save each as HTML Only:

| Save as | URL |
|---|---|
| `listing_p1.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing |
| `listing_p2.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing/-npage-2 |
| `listing_p3.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing/-npage-3 |
| `listing_p4.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing/-npage-4 |
| `listing_p5.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing/-npage-5 |
| `listing_p6.html` | https://www.santaclaraca.gov/business-development/development-projects/projects-listing/-npage-6 |

**2. Every project's detail page.** On each listing page, open each project in a new tab (Cmd-click the project name) and save it as HTML Only. Keep Chrome's default file name; the parser identifies projects by the page content, not the file name.

The detail pages are where the useful fields live:
- APN
- file number (PLN…)
- unit counts
- density
- status

If 57 saves is too tedious in one sitting, save the 6 listing pages first. I'll then generate a checklist of the 57 detail-page links from them.

Saved pages include City staff names and emails. The parser drops those fields, and the raw HTML is never committed.

## B. Phase 2 source documents (zoning capacity)

**Folder:** `data/manual/source_docs/` (gitignored). Every row of `config/zoning_rules.csv` will cite one of these, by section or table and page.

### B1. Zoning code: Title 18 (eCode360)

Start at https://ecode360.com/SA4626 and open Title 18 (Zoning). The code was comprehensively updated, so chapter numbers differ from the old links in City GIS. Use eCode360's print/PDF option for each chapter below and save it into `source_docs/zoning/`:

| Save as | Chapter |
|---|---|
| `t18_ch18-06_zoning_map_and_zones.pdf` | 18.06 (zones, and how they line up with General Plan designations) |
| `t18_ch18-10_residential.pdf` | 18.10 Residential zones |
| `t18_ch18-12_commercial.pdf` | 18.12 Commercial zones |
| `t18_ch18-14_mixed_use.pdf` | 18.14 Mixed-use zones |
| `t18_ch<NN>_industrial.pdf` | the chapter(s) for industrial / employment / office-R&D zones (check the Title 18 table of contents) |
| `t18_ch<NN>_public_open_space.pdf` | the chapter for public / quasi-public and open space zones |
| `t18_ch<NN>_planned_development.pdf` | the chapter for Planned Development (PD) and PD-MC |
| `t18_ch18-30_general_standards.pdf` | 18.30 Site planning and general development standards |

### B2. Specific plans and focus areas

Save each into `source_docs/specific_plans/`. Each row is the plan's official page; download the adopted plan PDF from it. If a plan's zoning or development-standards tables are in a separate document, save that too, with the same prefix.

| Save as | Page |
|---|---|
| `ecr_specific_plan_2026_adopted.pdf` | [El Camino Real Specific Plan](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/el-camino-real-specific-plan-revision). Click "View the Adopted Plan" (adopted May 19, 2026). |
| `patrick_henry_drive_sp.pdf` | [Patrick Henry Drive](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/patrick-henry-drive) |
| `tasman_east_sp.pdf` | [Tasman East](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/tasman-east). Get the latest revision; the page lists "Revised November 2020". |
| `lawrence_station_area_plan.pdf` | [Lawrence Station](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/lawrence-station). Get the latest version, including any boundary-expansion amendment. |
| `downtown_precise_plan.pdf` and `downtown_form_based_code.pdf` | [Downtown Precise Plan](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/downtown-precise-plan). Adopted Dec 5, 2023. |
| `santa_clara_station_area_sp.pdf` | [Santa Clara Station Area Specific Plan](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/santa-clara-station-focus-area-plan) |
| `freedom_circle.pdf` | [Freedom Circle](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/freedom-circle) |
| `stevens_creek_focus_area.pdf` | [Stevens Creek Boulevard Focus Area](https://www.santaclaraca.gov/home/showpublisheddocument/13934/639105681215570000) (direct PDF) |
| `old_ironsides_toc_rezonings.pdf` | [Old Ironsides TOC Rezonings](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/specific-plans/old-ironsides-transit-oriented-communities-toc-rezonings). New since Phase 0; it isn't one of the City GIS plan codes. |

### B3. General Plan (for the PD stand-in densities)

Save into `source_docs/general_plan/`:

| Save as | What |
|---|---|
| `gp_land_use_classifications.pdf` | The [Land Use Classifications](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/general-plan/land-use-classifications) page. Print it to PDF; it lists density ranges such as Medium Density Residential 20–36 du/ac. |
| `gp_ch5_land_use.pdf` | The Land Use chapter of the General Plan, from the [General Plan page](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/general-plan). Look for the designation table with densities and FARs. |

### B4. Housing Element sites inventory

This checks the State's 37-site / 7,821-unit copy against the City's own list. Save into `source_docs/housing_element/`:

| Save as | What |
|---|---|
| `he_2023-2031_certified.pdf` | The certified Housing Element (HCD found it compliant on May 31, 2024), from the [Housing Element page](https://www.santaclaraca.gov/our-city/departments-a-f/community-development/planning-division/general-plan/housing-element-update). |
| `he_sites_inventory.xlsx` (or `.pdf`) | The sites inventory appendix / Table A. Prefer the Excel version if one is offered. |
| `he_sites_amendment_2025.pdf` | The 2025 General Plan text amendment to the sites inventory list (Planning Commission, March/April 2025), if the page links it. |

## C. Contamination data (needed before Phase 3)

Per Phase 0 decision #6, I'll give you the exact download pages and file names for current GeoTracker and EnviroStor data **before Phase 3 starts**. Until then, the dated January 2023 Water Board copy is used only as a development placeholder.

## D. Email to the Planning Division (draft; you send it)

> **To:** planning@santaclaraca.gov
> **Subject:** Data request: export of the Development Projects listing
>
> Hello,
>
> I'm a student at Santa Clara University (Economics, Real Estate minor) building a non-commercial research project that maps development activity in Santa Clara using public data.
>
> I'd like to include the projects on the City's Development Projects listing page (santaclaraca.gov → Business & Development → Development Projects). Is there a downloadable version of that list (CSV or Excel), or a data feed? The fields that matter most are project name, address and APN, planning file number, residential units and non-residential square footage, and status. If the City already publishes this through an open-data portal or an ArcGIS layer, a pointer to it would be just as helpful.
>
> I'll credit the City as the source, and I won't republish staff contact information.
>
> Thank you for your time,
> [Your name]
> Santa Clara University, Class of [year]
