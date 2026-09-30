# Trail 21/22 route sources

Authenticated/source GPX bytes belong in this directory when acquired with verified provenance.

As of 2026-09-30, Trace de Trail's GPX export requires login, so no login-protected export is mirrored here. The public route pages do, however, embed the geometry required to render their maps. For source/year pairs already verified by date and geometry hash, that public map geometry is materialized as a **derived route reference** under `routes/ost/`:

- `trail22-2019` — Trace 69864
- `trail22-2022-2024` — Trace 165617, exact-geometry corroboration 203146/237224
- `trail22-2025-2026` — Trace 322314, exact-geometry corroboration 280053

These are not described as organizer-direct GPX files. The 2018 candidate Trace 7897 remains excluded because its `dateCompet` is 2016.

See `reports/materialized-public-route-assets.json`, `config/course-versions.json` and each route's provenance sidecar.
