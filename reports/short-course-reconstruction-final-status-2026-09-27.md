# Short-course reconstruction status — 2026-09-27

## Trail 5 / Naturloppet

Status: **validated reconstruction**, not organizer GPX.

The published reconstructed reference remains the 5.481 km route derived from the archived organizer raster and snapped to the archived OSM path network. It is closed at start/finish, with median route-to-organizer-raster deviation 34.3 m and p95 84.8 m.

A second, independent measurement now follows the full 971-point skeleton of the organizer's black route line directly in the georeferenced raster. It measures 5.545 km with a 25.6 m endpoint gap. The 64 m difference from the OSM-snapped reconstruction is small relative to the raster line thickness/path ambiguity and is retained as reconstruction uncertainty. The earlier 5.002 km value came from a coarse, non-persisted 62-vertex feasibility trace and is no longer the preferred raster-length check.

No accessible organizer GPX or verified participant GPX has yet been found for Trail 5. The 5.481 km asset is therefore publishable only as reconstructed reference geometry with explicit provenance.

## Trail 13/14

Status: **resolved as a validated organizer-raster reference**, not organizer GPX and not raw participant GPS.

The previous OSM composite is rejected. It incorrectly treated the complete Trail 5 loop as the western component and could not produce a source-supported eastern loop compatible with the other evidence. That path produced the blocked 14.948 km candidate and must not be used.

The replacement reconstruction follows the topology of the organizer's own archived 13/14 km raster directly. The raster is registered into SWEREF 99 TM through the independently cross-registered organizer maps. The selected topology measures **14.249 km** and passes the explicit topology QA.

Most importantly, direction is independently controlled by the 2023 Anna Karin Delborg race activity: her official result and watch time are both 1:31:44, her watch distance is 13.67 km, and her race note places Hallamölla 4.5 km from the finish. The raster-derived route places Hallamölla at km 9.725 with **4.524 km remaining**, without fitting the route length to her 13.67 km watch distance.

Independent local evidence also supports the eastern corridor: Christinehofs Ekopark publishes Hallamöllaleden as 8.5 km via Christinehof–Alunbruket–Verkeån–Hallamölla–Verkafuret–Verkasjön–Alunbruket–Christinehof, and a separate recorded 2011 GPS loop describes Christinehof–Alunbruket–Hallamölla–Verkasjön. Neither is labelled as an ÖST race GPX.

The 14.249 km asset can therefore be used for map display, segment projection and analysis when clearly labelled **reconstructed from georeferenced organizer map**. It must not be represented as an organizer GPX or exact participant recording.

## Version boundary

Geometry resolution and year identity are separate questions. The current organizer material supports the current reference geometry, but its map retains a legacy 13 km label/profile. Historical 13 km, 13+ km and modern approximately 14 km editions must not automatically be assigned the same course version. Year-specific grouping remains conservative until matching geometry evidence exists.

## Engineering status

- Authentic geometry still has precedence: organizer GPX > verified participant GPS > authoritative vector trail > georeferenced organizer-raster reconstruction > generic open-map reconstruction.
- Trail 13/14 now uses raster topology as route-choice authority; OSM is not allowed to override it where the graph conflicts with the organizer line.
- The rejected OSM map-match remains diagnostic only because it duplicated nearly 3 km of edges.
- Trail 5 has two independent derived geometry checks: organizer-raster skeleton 5.545 km and OSM-snapped organizer-raster reconstruction 5.481 km.
- Both short-course assets carry explicit provenance and must be presented as reconstructed references.
- Exact historical short-course course-version grouping remains unresolved rather than inferred from marketing distance labels.
