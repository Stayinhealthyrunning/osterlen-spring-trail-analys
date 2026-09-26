# Open-map fallback for ÖST short-course reconstruction — 2026-09-26

## Decision

A Lantmäteriet account is no longer a prerequisite for progressing the short-course geometry.

For the current Trail 5 reconstruction, use the evidence layers in this order:

1. **Organizer raster = route-choice authority.** The black organizer line decides which branch the race is intended to follow.
2. **OpenStreetMap raw vector data = primary no-account snapping geometry.** Export the small Christinehof bounding box and use OSM `highway=*` ways as the candidate path/road network.
3. **Independent participant GPS = canonical validation.** One race-day recording is the minimum promotion check; two matching recordings are preferred.
4. **Suunto trail-running heatmap = aggregate visual validation only.** It is valuable where two mapped paths are close, but a heatmap is not a race-day track and cannot by itself promote geometry to canonical status.
5. **Organic Maps = visual/offline QA.** Organic Maps is powered by OpenStreetMap and exposes hiking trails/walking paths; it is therefore a convenient human cross-check of the same underlying map family, not independent evidence from OSM.
6. **Google Maps/satellite = tertiary visual check.** Useful for obvious road/landscape alignment, but not the preferred machine-readable snapping source.

No service above should be allowed to override the organizer raster on route choice without independent race-day evidence.

## Trail 5 map frame

The merged raster prototype uses these approximate SWEREF 99 TM controls:

- south-west: E 432733 / N 6173751
- north-east: E 437965 / N 6176791

Transforming the two corners from EPSG:3006 to WGS84 gives the working OSM bounding box:

- west: 13.929567
- south: 55.704858
- east: 14.012122
- north: 55.732867

Christinehof gross-control point E 434707 / N 6175169 transforms to approximately 13.960636 E / 55.717867 N.

These values inherit the raster edge-coordinate uncertainty and are a retrieval/search envelope, not race-route vertices.

## OpenStreetMap retrieval

OpenStreetMap's own Export page supports raw XML export for a selected small area and links to Overpass for bounding-box downloads:

- https://www.openstreetmap.org/export

Direct small-area map API form:

`https://api.openstreetmap.org/api/0.6/map?bbox=13.929567,55.704858,14.012122,55.732867`

Equivalent Overpass query:

```overpass
[out:xml][timeout:60];
way["highway"](55.704858,13.929567,55.732867,14.012122);
(._;>;);
out body;
```

The repository helper `tools/extract_osm_path_network.py` converts such an `.osm` XML export into GeoJSON candidate ways while retaining the OSM way ID and tags.

## Why Organic Maps helps but does not replace OSM extraction

Organic Maps states that it is powered by OpenStreetMap and provides hiking trails and walking paths:

- https://organicmaps.app/sv/
- https://github.com/organicmaps/organicmaps

Its August 2026 release uses OpenStreetMap data updated to 2026-08-26:

- https://organicmaps.app/news/2026-08-31/

This makes Organic Maps excellent for manual QA on a phone/tablet. The machine-readable geometry should still be taken from OSM directly so provenance and exact OSM object IDs can be retained.

## Why Suunto helps

Suunto documents sport-specific heatmaps including trail running and states that heatmaps are created from publicly shared exercises:

- https://www.suunto.com/Support/Product-support/suunto_7/suunto_7/sports-by-suunto/suunto-maps/

That makes the heatmap a useful independent aggregate signal for ambiguous branches. It does **not** identify which heat belongs to ÖST, which year it came from, or whether users followed the exact race line. Therefore it is a corroboration layer, not canonical geometry.

## Participant-GPS status

The 2023 Anna-Karin D Trail 13/14 activity is public at:

- https://www.jogg.se/Traning/Pass.aspx?id=23408256
- https://www.jogg.se/Traning/GPSPass.aspx?adid=10988506

The pass page visibly offers "Exportera som GPX-fil", confirming that Jogg stores/export-enables GPS geometry for GPS-logged passes. Anonymous access does not expose the GPX file itself in the present environment. The participant explicitly reports 13.67 km / 1:31:44 for the race segment; the Jogg aggregate 15.55 km / 1:50:06 remains unsuitable as course distance.

Mathias Johansson's public Jogg calendar independently lists both "Ekopark trail 13 km med Glädjeknuff" and "Naturloppet 5 km med Glädjeknuff" on 2023-04-16. His diary contains Garmin Connect imports in general, but no exact public short-course pass/GPSPass URL has been recovered.

## Reproducibility correction

The merged Trail 5 prototype records 62 manually sampled image-space centreline vertices and a derived length of 5.002 km, but it does **not** persist the 62 vertex coordinates. The result is therefore a strong validation measurement but not a fully reproducible route trace.

Do not manufacture those vertices retrospectively. Either:

1. repeat the centreline digitization from the archived/native raster and persist every pixel vertex, or
2. acquire the OSM network first, select branches against the raster, and persist the resulting snapped OSM way sequence plus any explicitly raster-derived gaps.

The second route is preferred because it produces explainable geometry with source object IDs.

## Promotion rule

Trail 5 may currently be described as:

`validated_georeferenced_organizer_reference_geometry`

It must **not** be described as organizer GPX, participant GPS, or canonical race-day geometry.

Promotion to canonical race-day geometry requires:
- persisted geometry,
- route-choice agreement with the organizer raster,
- approximately correct course length and terrain narrative,
- and independent participant-GPS validation.

## Current hard blockers

The remaining blockers are external evidence/data availability, not method design:

- a route-specific OSM XML/Overpass extract has not yet been acquired by the current execution environment;
- the 62 prototype raster vertices were not persisted;
- no exportable Trail 5 participant race-day GPS has been found;
- the Trail 13/14 Jogg GPS registration is visible but its raw coordinate export has not been anonymously acquired.

No approximate or fabricated GPX should be introduced to close those gaps.
