# Short-course reconstruction status — 2026-09-27

## Trail 5 / Naturloppet
Status: **validated reconstruction**, not organizer GPX.

Current geometry is 5.481 km, closed at start/finish, with median route-to-organizer-raster deviation 34.3 m and p95 84.8 m. It is based on the archived organizer raster snapped to the archived OSM path network. No accessible organizer GPX or verified participant GPX has been found for this course/version. It may be used as reconstructed reference geometry, with provenance shown to users.

## Trail 13/14
Status: **unresolved — do not publish current candidate as validated route**.

The raster registration itself is stable and Hallamölla is independently controlled, but the available vector network and current composite hypothesis conflict with the independent 2023 participant distance. An exhaustive diagnostic comparison of 7,140 path pairs found no eastern Christinehof–Hallamölla loop shorter than 9.467 km in the current candidate graph. Combined with the 5.481 km western reconstruction, the minimum is 14.948 km, versus the 13.67 km participant observation.

This means at least one present assumption is insufficiently supported: the full Trail 5 loop may not be the western component of Trail 13/14; the OSM graph may omit a race-only/local path; or the legacy organizer raster/current course versions may differ. The engine must preserve this as an unresolved conflict rather than force geometry to 14 km.

## Engineering status
- Authentic geometry precedence is codified: organizer GPX > verified participant GPS > relevant official vector trail > raster/OSM reconstruction.
- Official Skåneleden GPX is segment evidence only and is never labelled ÖST GPX.
- Reconstruction workflow now uses pipefail so Python failures cannot be masked by tee.
- Strict Trail 13/14 QA is restored.
- Candidate diagnostics are persisted before a failed Action.
- Generic route-engine regression suite runs through GitHub Actions and passes.
- Trail 13/14 manifest forbids candidate GPX publication while unresolved.

## Remaining external evidence needed for Trail 13/14
Any one of these can materially resolve the geometry conflict: authentic organizer GPX for the relevant version; raw participant GPX from a known Trail 13/14 activity; another independently recorded participant trace; or an authoritative vector representation of Hallamöllaleden/local race-only paths that are absent from the archived OSM graph.
