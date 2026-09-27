# Frontend data delivery architecture — 2026-09-27

## Decision

Use **bootstrap + one selected-race bundle** as the browser data model.

Do **not** load the complete Engine 1.0 payload at application start.

The canonical monolithic Engine 1.0 export remains useful for:
- contract validation,
- reproducible handoff,
- offline analysis,
- debugging and archival comparison.

It is not the preferred browser transport.

## Measured baseline

Measured from the real frozen/curated dataset:

- 34 race editions
- 9,871 results
- 6,123 real split passages
- 300 Duo teams
- 599 Duo member rows
- 10 course versions in the current Engine export

Canonical payload:

- raw/minified JSON: **5,417,501 bytes (5.2 MiB)**
- gzip -9: **450,548 bytes (440.0 KiB)**

The transfer size is not alarming, but the browser would still need to parse and allocate a 5.2 MiB object tree containing every result and split before the user has selected a race. That is unnecessary work, particularly on mobile.

## Chosen delivery model

### Bootstrap

Contains only:
- Engine contract ID
- event metadata
- race catalog
- course metadata/provenance
- source/version metadata

Measured size:
- raw: **27,041 bytes**
- gzip: **1,980 bytes**

This is small enough to load immediately.

### Selected race bundle

One file per race edition, containing:
- race metadata/capabilities
- all result records for that edition
- checkpoint catalog
- real split passages for that edition
- Duo teams and member rows when applicable

Measured largest current edition:
- raw: about **329 KiB**
- gzip: about **29 KiB**

Measured bootstrap + largest race:
- about **31 KiB gzip**

This gives a very large margin for growth while avoiding a full 5.2 MiB JSON parse on first load.

## Why not split results and splits into even more files?

The largest complete selected-race bundle is only about 29 KiB gzip. Additional micro-sharding would add complexity, more HTTP requests and more cache bookkeeping without a meaningful current benefit.

Therefore:

- one selected-race data file is the default unit;
- route/elevation/replay assets remain separate;
- future purpose-built cross-year aggregate files may be added for history features if measurement shows they are useful.

## Route/elevation/replay

Always lazy-load:

- route geometry
- elevation profile
- replay interpolation data
- map-duel data

A race edition without an approved local route asset must never cause another year's route file to be fetched as a substitute.

## Cross-year/history features

Do not hydrate every race into memory at startup.

Preferred order:
1. bootstrap
2. selected race
3. on-demand history aggregate or additional race editions only when the user opens a cross-year feature

If repeat-runner identity is later implemented, its linkage/aggregate data should be a separate purpose-built layer rather than requiring all raw race records at startup.

## Performance budget

Machine-readable limits are in config/frontend-performance-budget.json.

Current data limits:

- bootstrap: <= 10 KiB gzip
- selected race: <= 75 KiB gzip
- selected race raw JSON: <= 600 KiB
- bootstrap + selected race: <= 100 KiB gzip
- monolithic Engine export regression guard: <= 750 KiB gzip

Provisional frontend limits, enforced once real frontend build artifacts exist:

- initial JavaScript: <= 256 KiB gzip
- initial CSS: <= 75 KiB gzip
- initial HTML: <= 32 KiB gzip
- critical first-load transfer: <= 512 KiB gzip

The critical-transfer budget excludes images, map tiles and lazy route/elevation/replay data.

## Build outputs

tools/export_engine_web_bundle.py produces:

- bootstrap.json
- manifest.json
- races/ost-YYYY-family.json

The output directory is transient and must not be committed. It is generated as a deployment/build artifact.

## Regression validation

tools/validate_frontend_performance_budget.py rebuilds the real web bundle in a temporary directory and fails CI when measured data exceeds the configured budget.

This means data growth cannot silently turn the application back into a monolithic, expensive first load.

## Browser-performance work during implementation

Transport budgets are now defined. When the frontend exists, add measured runtime tests for:

- JSON fetch + parse duration on a representative mobile device
- time to first useful race view
- chart construction time
- map initialization time
- replay memory footprint
- long-list rendering for 500+ result rows
- race-switch latency after cache warm-up

The goal is not arbitrary micro-optimization. The goal is to prevent unnecessary global hydration and to keep the selected-race interaction fast on mobile.
