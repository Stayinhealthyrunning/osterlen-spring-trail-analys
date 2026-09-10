# GPX source analysis

Haversine track length from source GPX. Route equivalence diagnostics use 50 m resampling and symmetric nearest-route corridor coverage. Raw elevation differences are unsmoothed and are not authoritative D+.

## Files

| File | Points | Calculated km | Raw D+ | Raw D- |
|---|---:|---:|---:|---:|
| `data/source/gpx/ultra60/ost-ultra60-2024-organizer.gpx` | 3258 | 60.598 | 0.0 | 0.0 |
| `data/source/gpx/ultra60/ost-ultra60-2025-2026-organizer.gpx` | 4246 | 59.621 | 1058.0 | 942.0 |

## Same-family geometry diagnostics

### `data/source/gpx/ultra60/ost-ultra60-2024-organizer.gpx` vs `data/source/gpx/ultra60/ost-ultra60-2025-2026-organizer.gpx`

- Geometry classification: **largely_same_corridor_with_changes**
- Distance difference: -0.98 km
- Start separation: 280 m; finish separation: 12 m
- Shared corridor within 50 m (symmetric minimum): 95.2%
- Shared corridor within 100 m (symmetric minimum): 98.2%
- A→B nearest distance median/p95: 16/48 m
- B→A nearest distance median/p95: 16/39 m

Divergence intervals over 100 m are recorded in the JSON report for course-change localization.

