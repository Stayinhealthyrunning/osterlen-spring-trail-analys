# Short-course geometry breakthrough — 2026-09-26

## Trail 5: organizer raster is georeferenceable

The organizer's current Naturloppet page embeds the direct image:

https://www.osterlentrail.se/uploads/4/1/8/7/41870619/st-5km-bana_orig.jpg

The raster is stronger evidence than previously recorded. It contains a north arrow, map scale and printed SWEREF 99 TM corner coordinates. The visible corner labels are approximately:

- south-west: N 6173751, E 432733
- north-east: N 6176791, E 437965

Therefore the black ÖST 5 km course line can be digitized into projected coordinates by affine georeferencing of the raster. This is **derived organizer-map geometry**, not an organizer GPX and not yet an actual race-day recording.

The organizer's current Race-PM independently states that the course is about 5 km, one lap in Christinehofs Ekopark, mainly gravel/forest roads plus about 2 km narrow trail. The older organizer programme adds that the first roughly 3 km are easy gravel/forest road, the last roughly 2 km are narrower/technical trail, with stairs on the finishing approach. Those descriptions are useful checks on any digitized line.

### Promotion rule

A digitized line may be stored as a reference geometry with provenance `derived_from_georeferenced_organizer_map`. It must not be promoted to canonical race-day geometry until checked against at least one independent participant GPS recording; two matching recordings are preferred.

## Trail 13/14: exact public GPSPass located

Anna-Karin D's 2023 race-day activity has a separate public Jogg GPSPass:

- GPSPass: https://www.jogg.se/Traning/GPSPass.aspx?adid=10988506
- parent activity: https://www.jogg.se/Traning/Pass.aspx?id=23408256
- date: 2023-04-16
- activity text: ÖST 13+ km
- participant-reported watch values: 13.67 km / 1:31:44
- Jogg aggregate values: 15.55 km / 1:50:06
- participant text says Hallamölla had 4.5 km remaining.

The discrepancy is important: the aggregate Jogg values must not be treated as course length until the underlying coordinate segmentation is inspected. The separate GPSPass nevertheless proves a GPS registration exists.

## Trail 5 participant search

Public-source searches have confirmed several high-value result anchors but have not yet exposed raw coordinates:

- Mathias Johansson explicitly reports running both Ekopark Trail 13 km and Naturloppet 5 km with Glädjeknuff on 2023-04-16.
- His public Jogg profile contains Garmin Connect imports, making him a plausible GPS source, but no indexed 2023 short-course GPSPass ID has yet been recovered.
- Leif Karlsson: 2024 Naturloppet 40:41, 2025 40:36; repeated participation makes him a useful continuity control if a public activity is found.
- Anders Persson's 2024 race report independently describes the stone stairs on the finishing approach, matching the organizer's historical course description.

No fabricated GPX has been created.

## Pixel-georeferencing prototype

A control reconstruction was performed against the 1000×738 public rendering of the organizer raster. The mapped frame was calibrated approximately to SWEREF 99 TM N 6173751 / E 432733 (south-west) and N 6176791 / E 437965 (north-east). An independent Christinehof castle position (about E 434707 / N 6175169 in EPSG:3006) falls at the expected castle location in the raster, providing an external gross-error check.

A manually sampled centreline of the thick black organizer course line (62 image-space vertices) measures approximately **5.002 km** after affine transformation. This is a prototype measurement, not a canonical GPX: vertex placement is based on the rendered raster and is not yet snapped to authoritative vector path geometry. The result is nevertheless a strong internal validation because it independently reproduces the advertised approximately 5 km course length.

The raster background itself is Lantmäteriet topography. The next refinement should therefore snap the reconstructed centreline to Topografi 10 road/path geometry (or trace the visible underlying mapped paths where vector access is unavailable), retaining the organizer line as the route-choice authority.
