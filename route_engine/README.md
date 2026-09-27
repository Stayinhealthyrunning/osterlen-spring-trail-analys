# Generic race-route reconstruction engine

> **Research-only prototype.** This directory is not the ÖST analysis runtime and is not part of the Engine 1.0 frontend build path. It is retained for route-reconstruction methodology/provenance only. Runtime course truth lives in `config/course-versions.json`.

Purpose: recover auditable race-course geometry when an original GPX is unavailable, while preserving the distinction between source geometry and reconstructed geometry.

## Pipeline

1. Discover organizer maps/GPX, historical pages, participant activities, local trail maps and course descriptions.
2. Archive source metadata, dates and provenance.
3. Georeference raster maps from printed grids, landmarks or control points.
4. Extract the visible race centreline and persist sampled vertices.
5. Acquire a vector path/road network.
6. Generate candidate graph paths from the raster/control observations.
7. Apply constraints: start/finish, checkpoints, distance, topology, named places, terrain narrative and year/version evidence.
8. Validate independently with participant GPS, GPS consensus, heatmaps, official local trails and imagery.
9. Score confidence per segment and retain ambiguous alternatives.
10. Export geometry plus a machine-readable provenance sidecar.

## Components

- source registry
- raster registration
- vector-network adapter
- candidate matcher
- constraint evaluator
- evidence scorer
- GPX/GeoJSON + provenance exporter

## Core rules

Distance match alone never proves a route.
Reconstructed geometry is never labelled organizer GPX.
Copied versions of one source count as one evidence family.
Ambiguous junctions remain explicit instead of being silently guessed.
Canonical status is scoped to a course version and supported year range.

## Segment confidence

A mostly certain course can contain one unresolved fork. Confidence is therefore stored per segment as well as for the complete route. Each segment records its evidence IDs, provenance class, decision reason and confidence.

## Calibration

ÖST Trail 5 is the current calibration case: the full organizer-raster skeleton measures 5.545 km and the OSM-snapped reconstructed reference 5.481 km. The earlier coarse 5.002 km prototype is superseded. Trail 13/14's former 14.249 km raster reconstruction is also superseded; the accepted working hypothesis is now a 13.472 km Hallamölla-splice recipe derived from verified Trail 21/22 geometry. The engine is intentionally race-neutral and remains upstream research tooling, not frontend code.

## Authentic geometry precedence

Route reconstruction is a fallback, never a replacement for authentic course geometry. For the relevant course/version, use organizer GPX directly when available. If organizer GPX is unavailable, prefer verified participant GPS (consensus before single trace). Official trail GPX may constrain only the race segments demonstrably sharing that trail; it must never be relabelled as race GPX. Raster/OSM reconstruction is permitted only for missing geometry or QA. Conflicts remain unresolved rather than being forced to a nominal distance.
