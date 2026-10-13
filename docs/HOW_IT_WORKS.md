# How It Works

A plain-English walkthrough of the system. It grows as the project is built. The full walkthrough and the "10 likely interview questions" section are written in Phase 8, once there's a real system to describe.

## Design decisions (and why)

### Where parcels come from
- **One master parcel layer.** The city publishes a "Land Parcels" GIS layer that already carries each parcel's APN, zoning, General Plan designation, specific-plan area, and year built. Starting from that one layer means fewer joins, and so fewer places for a parcel to fall through the cracks.
- **Retired parcels are dropped.** The city's parcel file keeps "retired" parcels (old lot lines replaced by newer ones) alongside active ones, and they overlap. Counting both would double-count land, so only active parcels are analyzed.
- **We download everything, then filter locally.** The city's map server sits behind a security firewall that blocked one of our filtered queries as if it were an attack. Asking for "all records" and filtering on our side avoids that, and it's just one request.

### Joining sources together
- **Every APN becomes 8 plain digits.** The same parcel is written `097-08-058` by the city, `09708058` by the county, and `06085_09708058` by the state. Converting all of them to `09708058` before joining means a parcel matches no matter which agency wrote it. Anything that doesn't clean up to exactly 8 digits is logged instead of guessed.
- **Measurements happen in feet, maps in lat/long.** Lot areas and "within ½ mile of a station" are computed in California State Plane coordinates, which are measured in feet. Doing the math in lat/long would distort distances. The map gets a lat/long copy at the end.

### Checking the data before trusting it
- **The two city layers must agree before they're joined.** The flood note lives on a layer with no parcel numbers, so it's joined by the city's internal record number. On every run the pipeline first checks that both layers list the same zoning, plan, and status for every record; in Phase 1 all 29,971 matched. If they ever drift apart, the pipeline stops instead of mixing up parcels.
- **Lot areas are computed, then compared with the city's published acreage.** Across 14,980 parcels with a published acreage, the median difference is 0.2%. The one big outlier is flagged in `docs/DATA_SOURCES.md`.
- **Condo common areas keep the city's own ID.** 313 shared condo grounds carry a city label like `097-90-00A`, which isn't a real assessor parcel number. They stay on the map so complexes don't show holes, but they're clearly labeled and never matched to county or state records.

### The map
- **The map data is a set of static files, not a database.** All 27,706 parcels fit in about 0.9 MB (compressed), so the app loads them directly from the website with no server or database to run or pay for. Parcel details (about 0.6 MB) load just after the map appears, so the map shows up first.
- **The zoning map uses three colors on purpose.** On a map any two colors can end up side by side, and more than three become hard to tell apart for colorblind viewers. So related zones share a color, and clicking any zone type in the legend highlights just that type.
- **Plan-area outlines are derived from parcels.** The city tags each parcel with its plan area but doesn't publish plan boundaries, so the pipeline merges each plan's parcels and fills in the streets between them to draw an outline.
- **Every parcel links to its exact source record.** The panel's "City GIS record" link opens the city's own data for that parcel, so any number on screen can be checked against the original.

### Housekeeping
- **The project lives outside iCloud.** The Desktop is synced to iCloud, which hid files inside the Python environment and broke it, and would also have uploaded hundreds of megabytes of build files. The project now lives in `~/Projects/softsite`, and GitHub is its backup.
- **One map file is copied at install time.** The mapping library runs part of its work in a separate background file, which the website bundler doesn't pick up on its own. A small script copies that file into the site on every `npm install`.

### Estimating what's built today
- **Building heights come from county LiDAR.** In 2020 the county flew a laser survey that measured the height of every building. That beats the free global building datasets, where only about three quarters of buildings have a height and almost none have a floor count. Floors are estimated as height ÷ a typical floor height, rounded down.

## System walkthrough

*(Written as phases complete.)*

## Likely interview questions

*(Written in Phase 8.)*
