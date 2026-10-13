# Methodology notes

This is working text for the public Methodology page, which is built in Phase 8. Every statement here must stay true to how the system is actually built. Update this file whenever a method changes.

## What SoftSite is (and isn't)

SoftSite is a **screening tool**. It is not a zoning determination, legal advice, or an appraisal. It points to parcels worth a closer look, using public data. Every number links to its source and retrieval date.

## Parcels

- **Source:** City of Santa Clara GIS "Land Parcels" layer.
- **Which parcels:** active parcels only; retired lot lines are removed.
- **APNs:** written uniformly as 8 digits so data from the city, county, and state lines up.
- **Lot area:** computed from the parcel shape in California State Plane coordinates (feet).

## Allowed intensity (Phase 2)

- **Zoning first.** Allowed density, FAR, and height come from the zoning code and adopted specific plans. Each rule carries a citation.
- **Planned Development (PD) parcels** have no fixed density in the zoning code. Each PD's own approved plan governs, and those plans aren't available as data. For PD parcels we use the **General Plan designation's density as a stand-in**:
  - it's labeled on every parcel (`density_basis = general_plan_pd_proxy`)
  - it's treated as an **upper bound**
  - it's marked **lower confidence**
  - users can exclude PD parcels from rankings
- **Builder's remedy projects can exceed both zoning and the General Plan.** Under the Housing Accountability Act (Gov. Code §65589.5(d)(5)), these projects can be approved above the limits the screener models. Santa Clara's Network Circle Residential Project (584 units on land designated for office/R&D) is one example. The screener **cannot predict** their capacity. They appear through the pipeline layer as **"In play."**
- **Airport height limits are not modeled (v1).** Parts of north Santa Clara sit near San José Mineta International Airport, where FAA and county airport land-use rules can cap building height below what zoning allows. No public GIS layer of those limits was available, so **capacity near the airport may be overstated**.

## What's built today

- **Building footprints and heights** come from the County of Santa Clara's 2020 LiDAR survey.
- **Floors** = roof height ÷ a typical floor-to-floor height, rounded down, with a minimum of 1:
  - 12 ft for residential
  - 15 ft for office/R&D, commercial, and mixed use
  - 24 ft for industrial

  The rule is calibrated against known buildings (see `docs/VALIDATION.md`).
- **Buildings finished in 2021 or later** may be missing or wrong in the 2020 survey. Those parcels are flagged.
- Overture Maps buildings are used as a cross-check.

## Score (Phase 3)

The score is a weighted sum of five components (weights in `config/scoring.yaml`). Underutilization includes **building age** (older scores higher), from the year-built field in City GIS.

## Hazards

- **Flood:** the City's parcel flood note (e.g., "parcel in multiple flood zones") plus the County's 100-year flood layer, a subset of FEMA's 2015 flood maps.
- **Contamination:** state cleanup-site databases (EnviroStor, GeoTracker). Each flag shows the date of the data it came from.
