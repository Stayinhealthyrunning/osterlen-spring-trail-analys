# Remaining open questions after data freeze

This file intentionally contains only issues that cannot be closed from the current verified source material. It is not a general backlog.

## 1. Generic Gotaleden engine integration

**Status:** waiting on external project state.  
**Blocker:** the generalized `Stayinhealthyrunning/gotaleden-splits` engine/refactor should stabilize before ÖST imports that core.  
**Next action:** build an adapter from `data/derived/ost-analysis-2018-2026.sqlite.gz` to the finalized generic engine contract. Do not recrawl Sportstiming.

## 2. Historical local route assets

**Status:** source comparability is stronger than frontend asset availability.  
**Known:** course-version evidence exists for historical Ultra and most Trail 21/22 years.  
**Missing:** locally usable/redistribution-appropriate route assets for several historical versions.  
**Effect:** split analysis is possible for historical Ultra/Duo, but route-dependent replay/map remains disabled unless a local route asset exists.

## 3. Trail 13/14 and Trail 5 historical course versions

**Status:** Trail 5 georeferencing is quantitatively validated as a reference; exact path snapping, participant-GPS validation and year-by-year assignment remain unresolved.  
**Known:** current organizer pages expose georeferenceable route-shape map images for both families. The Trail 5 raster has approximate SWEREF 99 TM frame controls, north arrow and scale. A 62-vertex manual centreline prototype measured 5.002 km after affine georeferencing, independently reproducing the advertised approximately 5 km course length. The 62 raw pixel vertices were not persisted, so this is a validation measurement rather than a reproducible canonical trace. A no-account fallback is now specified in `config/short-course-map-reconstruction.json`: organizer raster for route choice, raw OpenStreetMap `highway=*` ways for candidate vector geometry, Suunto heatmap/Organic Maps for QA, and participant GPS for canonical validation. For Trail 13/14, a verified 2023 race-day Jogg GPSPass (Anna-Karin D, adid 10988506) proves a participant GPS registration and explicitly reports 13.67 km / 1:31:44 for the race segment. The Jogg pass page exposes a GPX-export action, confirming GPS geometry exists, but the raw file has not been anonymously acquired.  
**Blocker:** raw route-specific vector geometry still cannot be transported from OSM/Overpass into the current execution environment; the Trail 5 prototype vertices were not persisted; Jogg GPX export requires paid membership; no independent exportable Trail 5 race-day GPS has been found; and no complete validated year-by-year short-course GPX archive exists. The reconstruction method itself is no longer a blocker.  
**Rule:** Trail 5 may be described as `validated_georeferenced_organizer_reference_geometry`. Any persisted raster-derived line must retain `derived_from_georeferenced_organizer_map` provenance until it is snapped/validated. Do not call it organizer GPX or race-day GPS, and promote it to canonical race-day geometry only after independent participant-GPS validation. Do not use Jogg's 15.55 km aggregate for the 2023 Trail 13/14 course because the participant explicitly reports 13.67 km for the race segment.

## 4. Trail 21/22 in 2018

**Status:** intentionally unassigned, with stronger race-day support than before.  
**Known:** candidate geometry is strongly compatible with the 2019 route. An independently published participant activity from race day 2018-04-14 records 22.03 km for “Österlen Spring Trail 2018”, supporting a roughly 22 km actually run course.  
**Blocker:** candidate Trace metadata is dated 2016, and the participant activity does not expose an anonymously acquired coordinate series, so exact year-specific geometry provenance is still not strong enough for formal 2018 assignment.

## 5. Duo leg attribution

**Status:** member rows imported; systematic leg-number attribution remains unresolved.  
**Known:** 599 published member rows are retained and `source_sequence` is preserved. A verified 2019 participant activity independently records Duo leg 2 at 26.29 km and states the teammate's first leg was nearly 33 km, supporting materially asymmetric relay legs.  
**Blocker:** one participant account does not validate that source row 1/2 always maps to leg 1/2 for every team/year.  
**Rule:** keep `leg_no = NULL` globally until stronger source/organizer evidence exists; do not hard-code Duo as 30+30 km.

## 6. Historical gender / age gaps

**Status:** source limitation.  
**Known:** 2022 has explicit age/gender categories; 2024–2026 have nearly complete exact age/sex.  
**Missing:** reliable published sex/age fields for individual results in 2018, 2019 and 2023 in the frozen public structures.  
**Rule:** never infer these fields from names.

## 7. Cross-year person identity / repeat runners

**Status:** not implemented by design.  
**Blocker:** names alone are not a guaranteed stable identifier.  
**Required method:** separate derived linkage table with normalized evidence, confidence, ambiguity handling and an explicit distinction from source-local participant identity.

## 8. Physical interpretation of Bengtemölla 2022–2023

**Status:** timing observations are known; physical interpretation is not.  
**Known:** `32 km` and `Bengtemölla` are separate published readings with a large/variable elapsed gap.  
**Hypothesis:** approach/prewarning followed by a later station-related reading is plausible.  
**Rule:** expose the gap only as a service-window/between-observation candidate until timing-mat placement or organizer documentation verifies the physical meaning.

## Explicitly not open anymore

The following are completed and must not be reintroduced as backlog items:

- full Sportstiming result import for 2018–2026;
- frozen source archive and checksums;
- archive data-quality audit;
- explicit DNF resolution where source evidence exists;
- curated engine database;
- Ultra split normalization;
- Duo team split parsing;
- Duo member-row parsing;
- safe recovery of start number, club/country and source-backed 2022 age/gender category;
- course-version model for Ultra and Trail 21/22 except the documented unresolved years;
- engine-readiness matrix.
