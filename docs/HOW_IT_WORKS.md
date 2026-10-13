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

### Estimating what's built today
- **Building heights come from county LiDAR.** In 2020 the county flew a laser survey that measured the height of every building. That beats the free global building datasets, where only about three quarters of buildings have a height and almost none have a floor count. Floors are estimated as height ÷ a typical floor height, rounded down.

## System walkthrough

*(Written as phases complete.)*

## Likely interview questions

*(Written in Phase 8.)*
