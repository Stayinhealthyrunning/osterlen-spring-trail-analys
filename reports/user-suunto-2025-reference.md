# 2025 user Suunto barometric reference

A race-day GPX supplied by the project owner was inspected as an independent route/elevation reference for the 2025 Ultra. The user states that its elevation values come from the watch barometer.

## Source integrity

- Original filename: `suuntoapp-Running-2025-04-12T07-59-46Z-route.gpx`
- SHA-256: `007c9f007f12c9f5a0a42d9a6cb41240f2a6aec06afd06cbd2bed238d205db2a`
- Size: 1,263,810 bytes
- GPX structure: 20,508 route points (`rtept`), no timestamps
- Elevation values present: 20,465; missing: 43

The original activity file is not mirrored in the public repository. Analysis-ready, privacy-minimized derived metadata/profile data are stored in `data/source/gpx/ultra60/ost-ultra60-2025-user-suunto-barometric-reference.json` and `ost-ultra60-2025-user-suunto-geometry-summary.json`.

## Geometry diagnostics

The extremely dense point stream contains enough small horizontal GPS jitter that a naïve point-to-point sum is too long: **61.100 km**. A 5 m Douglas–Peucker simplification retains 858 points and gives **59.989 km**, which is a much more plausible route-length estimate and is close to the published/organizer 2025 route length.

This is diagnostic evidence only: organizer geometry remains the route source of record where available.

## Barometric elevation

The dense raw elevation stream must not be summed point-to-point for D+: doing so produces about **3,041 m ascent**, an obvious noise artefact for this course.

Using the same simplified horizontal route and resampling the elevation profile by distance gives strong method sensitivity:

| Elevation profile step | Derived ascent | Derived descent |
|---:|---:|---:|
| 25 m | 902 m | 781 m |
| 50 m | 876 m | 754 m |
| 100 m | 811 m | 688 m |

Therefore the file is valuable as a **barometric profile-shape reference**, but its D+ is not an official standalone number. Cross-year elevation comparisons should use one common filtering and/or DEM method.

## Landmark alignment

Projecting already catalogued Trace de Trail waypoint coordinates onto the 5 m-simplified race recording gives:

- **Bengtemölla: 33.533 km** (Trace/public reference ≈33.6 km)
- **Vantalängan: 51.457 km** (Trace/public reference ≈51.4 km)

The Bengtemölla coordinate lies only about 1.2 m from a recorded route point. This provides independent race-day geometry support for interpreting the 2024–2026 Sportstiming **34 km** passage as the rounded Bengtemölla timing location, while preserving the original `34 km` source label in normalized data.
