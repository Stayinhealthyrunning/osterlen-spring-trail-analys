# Loppanalys route-artifact contract

> **Research boundary:** this document describes an upstream route-artifact concept, not the active ÖST Engine 1.0 runtime contract. `config/course-versions.json` and the Engine 1.0 export are authoritative for the large build.

The reconstruction engine should be an upstream data tool, not frontend code.

A race project consumes a versioned route package:

```
routes/<race>/<course-version>/
  route.geojson
  route.gpx
  provenance.json
  qa.json
  alternatives.geojson
  elevation.json
```

When a course version has an approved local route asset, `route.geojson` and/or `route.gpx` contain selected geometry. A recipe-only provisional reference, such as the current Trail 13/14 working hypothesis, intentionally has no frontend route asset. `provenance.json` records source classes and evidence per segment. `alternatives.geojson` retains unresolved forks rather than hiding them. `qa.json` records validation results. Elevation is separate because elevation providers and smoothing can change without changing horizontal course geometry.

## Frontend statuses

A Loppanalys frontend should display one of:

- source route
- validated reconstructed route
- reconstructed candidate
- route partly unresolved

The UI should not call all four simply "GPX".

## Shared-engine boundary

Race-specific repositories provide manifests and evidence. The shared engine provides adapters, matching, scoring, ambiguity handling, QA and export. This makes ÖST a calibration project rather than the permanent home of the engine.

## Migration path

1. Finish calibration against ÖST Trail 5 and Trail 13/14.
2. Test against one race where a trusted organizer GPX already exists by hiding the GPX, reconstructing from weaker evidence, then comparing the result with the withheld truth geometry.
3. Tune matching/scoring thresholds from measured reconstruction error.
4. Move `route_engine/` into the shared Loppanalys/Gotaleden core.
5. Keep only race manifests/evidence in individual race repositories.

The withheld-GPX test is essential: it measures whether the engine actually reconstructs routes accurately rather than merely producing plausible-looking tracks.
