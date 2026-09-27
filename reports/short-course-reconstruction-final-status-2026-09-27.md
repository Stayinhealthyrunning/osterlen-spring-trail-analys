# Short-course reconstruction status — 2026-09-27

## Trail 5 / Naturloppet
Status: **validated reconstruction**, not organizer GPX.

Current geometry is 5.481 km, closed at start/finish, with median route-to-organizer-raster deviation 34.3 m and p95 84.8 m. It is based on the archived organizer raster snapped to the archived OSM path network. No accessible organizer GPX or verified participant GPX has yet been found for this course/version. It may be used as reconstructed reference geometry with provenance shown to users, but exact year-by-year identity remains unassigned.

## Trail 13/14
Status: **validated reconstructed 2023-family reference; exact 2026 version unconfirmed**.

The previous blocker was caused by the reconstruction model rather than by contradictory course evidence. That model incorrectly forced the complete Trail 5 reconstruction into the Trail 13/14 route and then required the eastern loop to be completed solely through the archived OSM graph. The graph could not represent the organizer route and produced a minimum 14.948 km composite.

The replacement method reconstructs the route directly from the georeferenced organizer raster. The raster skeleton contains one principal eastern cycle and two western start/finish arms attached at the central junction. With a 4 px Ramer–Douglas–Peucker simplification tolerance — approximately the organizer line's own mean width of 3.592 px — the resulting reference geometry is **13.664 km** with 73 route points and a 35.7 m start/finish separation.

Independent validation is unusually strong: Anna Karin Delborg's 2023 public GPS activity reports **13.67 km / 1:31:44**, and the official ÖST result has the same participant at exactly **1:31:44**. The participant distance was not used as geometry input; the reconstructed route differs by only **5.9 m**. Map registration is also stable (median 0.24 px, p95 1.57 px).

The route is therefore publishable as a **derived reconstructed reference geometry**, with explicit provenance. It must not be called an organizer GPX or participant GPX. Because the current event is marketed as approximately 14 km while the embedded organizer image retains a legacy 13 km label, exact equivalence with the 2026 route remains unconfirmed until a current organizer/participant GPS trace is obtained.

## Engineering status
- Authentic geometry precedence remains: organizer GPX > verified participant GPS > authoritative local vector trail > georeferenced organizer-raster reconstruction > open-map fallback.
- Trail 13/14 no longer depends on the incomplete OSM topology for primary geometry.
- The raster-native Trail 13/14 reconstruction is reproducible in `tools/reconstruct_trail14_raster.py`.
- CI reconstruction and both short-course QA gates pass.
- Trail 13/14 provenance records that the participant distance is validation only and was not used to fit the geometry.
- The legacy OSM candidate frontier remains diagnostic evidence explaining why the former model failed.

## Remaining external evidence
For Trail 13/14, new external evidence is now needed mainly to confirm **exact course-version identity and direction**, not to obtain a usable reference shape: a current organizer GPX, a current participant race-day GPX, or another independently recorded trace would resolve the 2026 question.

For Trail 5, participant/organizer GPS remains the main missing evidence for promotion beyond reconstructed reference geometry.
