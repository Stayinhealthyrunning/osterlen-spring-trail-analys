# Short-course reconstruction status — 2026-09-27

## Trail 5 / Naturloppet

Status: **validated organizer-raster reconstruction**, not organizer GPX.

A source-control error has been corrected: the organizer map prints the upper-right SWEREF 99 TM easting as **E 437465**. The previous reconstruction used **E 437965**, which stretched the map 500 m eastward. With the corrected frame and minimal centreline simplification, the organizer-raster route is **5.003 km**. This independently reproduces the earlier manual georeferenced control of **5.002 km** to within **0.8 m**.

The route is now taken directly from the organizer raster. OSM is secondary corroboration only and is no longer allowed to pull the course away from the organizer line. Start/finish gap is 25.2 m; OSM vertex deviation is median 30.4 m and p95 60.2 m.

## Trail 13/14

Status: **validated organizer-raster family/reference geometry for the legacy 13 km map**. It is not yet proof that the current marketed 14 km course is exactly identical.

The old 14.948 km blocker is resolved. It was caused by two wrong assumptions: the same +500 m east-coordinate transcription error and a model that incorrectly composed the full Trail 5 loop with an eastern Hallamölla loop.

The 13 km organizer raster contains its own western loop, a shared Christinehof–Verkeån connector and an eastern Hallamölla loop. Reconstructing that topology directly from the organizer centreline gives **13.084 km** after removing one-pixel raster staircase noise. Cross-registration between the 13 km and 5 km organizer maps is strong (median 0.24 px, p95 1.57 px).

Hallamölla is only **9.6 m** from the reconstructed line and occurs at km **8.451**, leaving **4.634 km** to finish. This independently agrees closely with the 2023 participant description that Hallamölla was reached with about 4.5 km remaining. The participant's watch distance of 13.67 km is retained as corroboration, not used to stretch the geometry.

## Route-use policy

- Authentic geometry precedence remains: organizer GPX > verified participant GPS > organizer map-derived geometry > supporting official/open vector trails.
- Trail 5 and Trail 13/14 reference GPX files are derived from organizer rasters and must never be labelled organizer GPX.
- OSM and the official Skåneleden GPX are corroboration/segment evidence, not substitutes for the visible organizer route.
- Trail 13/14 can now be shown as a provenance-labelled family/reference route; it must not be presented as proof that every historic 13 km edition or the modern 14 km edition is identical.
- Year-specific assignments remain independently gated by version evidence.
- The reconstruction workflow runs the generic route-engine regression suite and rejects future reintroduction of the E 437965 calibration.

## Remaining evidence gaps

No geometric conflict remains for the short-course reference routes. What remains is **version provenance**, not missing route geometry: an authentic organizer or participant raw GPX would raise source quality and could prove specific year identities. Until then, the tool can use the reconstructed reference lines with their provenance labels while keeping year-specific identity claims conservative.
