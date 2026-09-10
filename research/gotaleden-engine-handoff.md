# ÖST → generalized Gotaleden engine handoff

## Purpose

This repository owns Österlen Spring Trail source acquisition, provenance, normalization, course-history decisions and the completed source-side analysis database. The generalized frontend/analysis engine being developed in `Stayinhealthyrunning/gotaleden-splits` should be reused after that refactor stabilizes rather than copied prematurely.

The machine-readable handoff contract is `config/engine-adapter.json`.

## Start here — source-side work is already complete

Do **not** begin the engine integration by recrawling Sportstiming.

Primary engine handoff:

`data/derived/ost-analysis-2018-2026.sqlite.gz`

Immutable source/provenance archive:

`data/archive/ost-results-2018-2026.sqlite.gz`

The curated database currently contains 34 race-year instances, 9 871 results, 9 571 individual participant rows, 300 Duo teams, 599 published Duo member rows, 6 123 observed split passages and 699 derived metrics. `reports/engine-readiness.json` describes actual feature/field availability race by race.

## What remains ÖST-specific

- Sportstiming provenance and future refresh/import logic.
- Year/race-family catalogue from 2018 onward, including cancelled 2020/2021 editions.
- Checkpoint-label normalization by year.
- Duo source parsing and Bengtemölla exchange semantics.
- Trace de Trail/organizer route provenance and course-version evidence.
- Cross-year identity/linkage methodology.
- Capability/readiness rules that prevent unsupported features from appearing.

## What should come from the generalized engine

The Gotaleden frontend concepts already match ÖST well: dynamic races, indexed records/splits, multiple course assets keyed by course version, distinction between analysis boundaries and replay anchors, replay interpolation only between real timing passages, and whole-course comparison gating.

Expected payload concepts are:

- `race_catalog`
- `courses`
- `races`
- `checkpoints`
- `teams`
- `splits`
- route/elevation bundles keyed by `course_version`

`config/engine-adapter.json` contains the field-level contract and the mapping from the curated SQLite layer.

## Critical ÖST differences the engine must tolerate

### Multiple years and changing course geometry

`race_family` never implies geometric equality. A race instance gets a `course_version` only from verified route evidence in `config/course-versions.json`.

- Same course version → verified same geometry for whole-course comparison.
- Explicit comparison group → compatible comparison only under the documented methodology.
- No shared version/group → no record/whole-course comparison as if the courses were identical.

### Sparse checkpoint layouts

Ultra has intermediate timing but the layout changes by era:

- 2018–2019: Stenshuvud, Bengtemölla, Vantalängan, finish.
- 2022–2023: `32 km`, `Bengtemölla`, finish.
- 2024–2026: `34 km`, finish; route evidence maps 34 km to Bengtemölla.

The full imported public result archive did not expose intermediate split tables for Trail 21/22, Trail 13/14 or Trail 5. The UI must therefore remain useful with finish-only timing and must not synthesize intermediate passages.

### Bengtemölla 2022–2023

Do not collapse `32 km` and `Bengtemölla`. They are separate published observations. The gap is stored as a derived `bengtemolla_service_window_seconds` candidate where possible, but physical mat placement is not verified. It must not be presented as confirmed stationary aid-station dwell time.

### Duo

Duo uses the same full route/course version as same-year Ultra. Do not model it as two hardcoded 30.000 km legs.

The source-side Duo adapter is now implemented to the safe level supported by the public data:

- team results are normalized;
- 741 real team split passages are stored;
- 599 published member rows are stored;
- member `source_sequence` is retained;
- `leg_no` remains NULL because available evidence does not prove that source row order always equals leg 1/2.

The engine may display team/member source data, but must not invent leg attribution.

### Field coverage varies by era

- Bib/start number is now recovered for all 9 871 result rows.
- 2022 individual categories explicitly encode sex + age band and are used as such.
- 2024–2026 have nearly complete exact age/sex from public details.
- 2018, 2019 and 2023 do not expose reliable sex/age in the frozen public structures; those fields stay missing.
- Exact age is never inferred from an age band.

The frontend must treat missing demographic fields as missing data, not as zero or unknown-by-name inference.

## Route-data policy

There are two separate concepts:

1. **Geometry evidence for historical comparability.** Public map geometry may establish fingerprints/overlap/course-version evidence without being redistributed.
2. **Route asset distributed with the site.** Map/replay requires a locally usable route asset with suitable provenance/redistribution basis.

Current local route assets make Ultra and Duo 2024–2026 replay/map-ready. Older Ultra/Duo years can already support split analysis but remain blocked for route-dependent replay/map until a usable local route asset exists.

## Capability gating

Use `reports/engine-readiness.json` as the current runtime-facing truth. It is built from the curated database rather than from race-name assumptions.

Current overall state:

- 34 race-year instances with results.
- 13 race-year instances with real split analysis data.
- 6 race-year instances with splits + local route data sufficient for replay/kartduell.
- 19 race-year instances with verified course version.

UI rule: hide unavailable functions or show a short factual explanation. Never fill empty analyses by inference.

## Recommended integration sequence after Gotaleden core stabilizes

1. Freeze the generic Gotaleden engine/data-adapter version to be reused.
2. Add an ÖST adapter that reads the curated SQLite contract and emits the engine payload; do not recrawl source data.
3. Build course bundles only for course versions with usable local route assets.
4. Map checkpoints using `config/checkpoint-normalization.json` while retaining source labels.
5. Test at least 2018 Ultra, 2023 Ultra (double Bengtemölla timing), 2025 Ultra, 2026 Trail22 (finish-only) and one Duo year.
6. Gate features from `reports/engine-readiness.json`, not hardcoded family names.
7. Add cross-year views only after course-version constraints and a separate repeat-runner identity/linkage method are tested.

## Acceptance criteria

The source-side handoff is already considered ready because:

- all 34 held race-year instances have stable bindings and stored results;
- source provenance is frozen and auditable;
- all emitted splits are published observations;
- Duo team/member structures are stored without unsupported leg assignment;
- course-version semantics are explicit;
- map/replay eligibility is data-driven;
- finish-only races remain representable;
- 2020/2021 are explicit cancelled years;
- unresolved geometry, demographic and identity issues are represented as limitations rather than inferred data.

The next substantive project step is therefore **generic engine integration**, not source discovery or production result import.
