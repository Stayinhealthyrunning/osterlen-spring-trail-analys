# Route elevation evidence

Source-specific elevation evidence extracted from existing verified route sources. These values are **not** a harmonized cross-year D+ series.

## Trace de Trail

| Family | Year | km | profile pts | elev min–max | D+ | D- | provenance |
|---|---:|---:|---:|---:|---:|---:|---|
| `trail22` | 2018 | 21.688 | 1515 | 19–126 m | 482 | 482 | date mismatch ⚠ |
| `trail22` | 2019 | 21.726 | 1344 | 19–126 m | 475 | 475 | year-match |
| `trail22` | 2022 | 21.741 | 837 | 34–139 m | 329 | 328 | year-match |
| `trail22` | 2023 | 21.741 | 837 | 34–139 m | 329 | 328 | year-match |
| `trail22` | 2024 | 21.741 | 837 | 34–139 m | 329 | 328 | year-match |
| `trail22` | 2025 | 21.710 | 1395 | 34–139 m | 254 | 255 | year-match |
| `trail22` | 2026 | 21.710 | 1395 | 34–139 m | 254 | 255 | year-match |
| `ultra60` | 2018 | 62.055 | 2218 | 0–116 m | 1227 | 1152 | year-match |
| `ultra60` | 2019 | 58.612 | 2271 | 0–124 m | 851 | 736 | year-match |
| `ultra60` | 2022 | 58.347 | 2224 | 0–124 m | 838 | 721 | year-match |
| `ultra60` | 2023 | 58.347 | 2224 | 0–124 m | 838 | 721 | year-match |
| `ultra60` | 2024 | 60.598 | 2240 | 0–124 m | 693 | 578 | year-match |
| `ultra60` | 2025 | 59.592 | 4246 | 0–121 m | 680 | 564 | year-match |
| `ultra60` | 2026 | 59.592 | 4269 | 0–121 m | 683 | 567 | year-match |

## Local organizer GPX

| File | km | raw D+ | raw D- | elevation range |
|---|---:|---:|---:|---:|
| `data/source/gpx/ultra60/ost-ultra60-2024-organizer.gpx` | 60.598 | 0 | 0 | 0–124 m |
| `data/source/gpx/ultra60/ost-ultra60-2025-2026-organizer.gpx` | 59.621 | 1058 | 942 | 0–121 m |

## Interpretation

- Trace values are valuable historical source evidence and can supply route-profile metadata where an organizer GPX lacks elevation.
- The 2024 organizer GPX has incomplete elevation and a raw D+ of 0 in the current parser, while the matching Trace route exposes a complete profile summary and cumulative +693/-578 m.
- The 2025/2026 organizer GPX raw +1058/-942 m differs materially from Trace (+680/-564 in 2025; +683/-567 in 2026), demonstrating method dependence rather than a trustworthy cross-source D+ identity.
- Therefore the public product should keep source-specific values for transparency and use a separately standardized DEM-derived profile for cross-year comparisons.
