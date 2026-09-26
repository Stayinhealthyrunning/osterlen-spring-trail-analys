# Lantmäteriet snap reconstruction method — short courses

## Result of feasibility test

The method is feasible and is now the preferred reconstruction method for Trail 5 when no direct organizer GPX or independently exportable race-day GPS is available.

The organizer's published 5 km raster is itself based on a Lantmäteriet topographic map. The thick black race line therefore identifies route choice against an authoritative underlying road/path network rather than against an unrelated schematic basemap.

Lantmäteriet's current **Topografi 10 Nedladdning, vektor (2026.05)** is the preferred geometry source. It is intended for approximately 1:1,000–1:20,000 use, is delivered as GeoPackage in SWEREF 99 TM, and contains road/path geometry. The communication theme exposes:
- `vaglinje`
- `ovrig_vag`
- object classes including Parkväg, Cykelväg, **Gångstig**, Elljusspår and Traktorväg.

For `ovrig_vag`, Lantmäteriet states positional uncertainty requirements of approximately:
- cycle/park path: 2 m
- tractor road: 5 m
- walking path: 10 m

The organizer raster should therefore be used to select the correct branches, while the final reconstructed line should follow the Lantmäteriet vector geometry wherever the race line clearly corresponds to a mapped road/path.

## Reconstruction pipeline

1. Archive the original organizer raster bytes and SHA-256.
2. Determine exact raster map-frame pixel bounds and read the printed SWEREF 99 TM edge coordinates from the original pixels; do not rely on a browser-rescaled screenshot.
3. Fit the raster-to-SWEREF affine transform and record residual/error checks.
4. Load Topografi 10 `vaglinje` and `ovrig_vag` for the Christinehof corridor.
5. Digitize only coarse control points along the center of the organizer race line.
6. Build a candidate graph from Lantmäteriet road/path segments inside a tolerance corridor around those controls.
7. Solve for the connected path through that graph that best follows the organizer line, with explicit handling of start/finish at Christinehof.
8. Where the race line leaves mapped Lantmäteriet geometry, retain a separately flagged raster-derived segment rather than forcing it onto a wrong path.
9. Compare total length with the organizer description “omkring 5 km” and with independent race reports/participant GPS if obtained.
10. Store the result as `reconstructed_from_georeferenced_organizer_map_and_lantmateriet_topografi10`, never as `organizer_gpx` or `participant_gps`.
11. After horizontal geometry is accepted, sample the common Lantmäteriet terrain model under the reconstructed line for standardized elevation.

## Important limitation discovered during the test

Do not derive the affine transform from coordinates transcribed by eye from the web-rendered image. Browser/image resizing makes that unnecessarily error-prone. The original raster must be archived first and its printed frame coordinates read at native resolution.

## Trail 13/14

The legacy-labelled organizer image `13km-bana-h-jdkurvan-3_orig.jpg` was inspected during the feasibility test. It is also a Lantmäteriet-based map with printed SWEREF 99 TM edge coordinates, north arrow and scale. It is therefore independently georeferenceable by the same method.

The image also contains a plotted elevation profile with a horizontal axis from 0.0 to 13.0 km and shows the long eastern Hallamölla/Verkeån section plus a western Christinehof loop. Visually, that western loop follows the same Christinehof/Södre-vång corridor shown much more tightly in the organizer's 5 km raster. This gives a valuable second organizer-map registration for the 5 km corridor at a different map extent/scale.

Use the two raster registrations as a consistency check on branch selection and affine georeferencing. They are not independent race-day sources because both are organizer maps. The 2023 Anna-Karin D GPSPass remains independent participant evidence for the Trail 13/14 family.

## Evidence classification

A route reconstructed this way can be high-quality analysis geometry because the selected path follows authoritative mapped road/path objects. It remains a reconstruction. Promotion to canonical race-day geometry should require an independent check (participant GPS, multiple race-day observations, or equivalent evidence).
