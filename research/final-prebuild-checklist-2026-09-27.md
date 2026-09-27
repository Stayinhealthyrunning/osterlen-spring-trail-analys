# ÖST – final prebuild checklist 2026-09-27

## Goal

This is the working checklist for starting the large ÖST Analys build. The source/data phase is considered complete enough to begin Engine 1.0 integration. Remaining source questions must not block the build unless they affect correctness of a feature that is actually enabled.

## Frozen inputs

- Primary engine input: `data/derived/ost-analysis-2018-2026.sqlite.gz`.
- Immutable provenance archive: `data/archive/ost-results-2018-2026.sqlite.gz`.
- Race/year model: 34 held race instances, 2018–2026 with 2020/2021 explicitly cancelled.
- Results: 9,871.
- Observed split passages: 6,123.
- Duo member rows: 599.
- Runtime feature gating: `reports/engine-readiness.json`.
- Course-version source of truth: `config/course-versions.json`.

Do not recrawl Sportstiming merely to begin the build.

## Route state at build start

### Ultra 60 / Duo 60
- 2018, 2019, 2022–2023: verified public geometry for course identity/comparability, but no redistributable local route asset.
- 2024: archived organizer GPX.
- 2025–2026: archived organizer GPX.
- Duo inherits same-year Ultra geometry.

### Trail 21/22
- 2019: verified public geometry.
- 2022–2024: exact identical public geometry.
- 2025–2026: exact identical public geometry.
- 2018 remains unassigned because candidate Trace metadata is dated 2016.

### Trail 13/14
- The former 14.249 km raster reconstruction is **superseded** after visual inspection showed systematic corridor displacement.
- Accepted working hypothesis: **13.472 km Hallamölla splice reference**.
- Recipe: start on verified Trail 21/22 2022–2024 geometry, keep it to the first Hallamölla passage, remove the 8.269 km eastern loop between two nearly identical Hallamölla passages (0.18 m separation), then continue on the same verified geometry to finish.
- Derived distances: start→Hallamölla 8.687 km; Hallamölla→finish 4.784 km.
- This agrees well with the verified 2023 participant activity: watch distance 13.67 km and note of about 4.5 km remaining at Hallamölla.
- **No redistributable/local Trail 13/14 route asset is treated as authoritative.** Authentic organizer/participant GPX remains a priority source improvement.

### Trail 5
- 2026 working reconstruction: 5.481 km.
- Independent full organizer-raster skeleton: 5.545 km.
- Historical exact identity remains unresolved.

## Engine integration sequence

1. Freeze a baseline export from the curated SQLite database and validate row counts/status totals.
2. Implement the ÖST adapter to Engine 1.0 without touching acquisition code.
3. Materialize event, race catalog, race editions, participant/competition semantics and capabilities.
4. Verify finish-only behavior for Trail 21/22, Trail 13/14 and Trail 5: no synthetic splits or replay.
5. Build checkpoint payloads for Ultra/Duo from `config/checkpoint-normalization.json`.
6. Build local route bundles only where route assets are allowed by `config/course-versions.json`.
7. Enable replay/map duel only for editions that pass the readiness contract.
8. Add explicit UI methodology labels for provisional/reconstructed geometry.
9. Add cross-year course-record views only where course-version comparability is verified.
10. Add identity/history views only after a separate repeat-runner linkage layer has its own confidence/evidence tests.

## Required acceptance cases

Before calling the first integrated build trustworthy, test at least:

- Ultra 2018: historical splits work, route replay stays unavailable.
- Ultra 2023: 32 km and Bengtemölla remain separate observations.
- Ultra 2025: results + splits + route/replay available.
- Duo 2025: team semantics and member rows render; no guessed leg assignment.
- Trail 22 2026: finish/result/course-version views work; split/replay stay disabled.
- Trail 14 2026: working course reference may be described, but no authoritative public GPX/replay is claimed.
- Trail 5 2026: reconstructed route is explicitly labelled as reconstructed.

## Non-blocking source improvements

Continue opportunistically, without delaying integration:

- Find authentic participant/organizer GPX for Trail 13/14, ideally two independent participant tracks for the same year.
- Find authentic Trail 5 GPX.
- Resolve Trail 22 2018 year-specific provenance.
- Obtain local/redistributable historical Ultra/Trail22 route assets where possible.
- Verify Duo member-to-leg assignment from explicit source evidence.
- Verify physical timing-mat interpretation around Bengtemölla 2022–2023.

## Hard rules during build

- Missing data stays missing.
- Marketing distance is not geometry identity.
- A course-version assignment does not automatically grant a route asset.
- Public third-party geometry used for diagnostics must not silently become a redistributable frontend route.
- No inferred age/sex from names.
- No inferred Duo leg assignment from row order.
- No inferred cross-year person identity from name equality.
- Correctly disabled functionality is preferable to invented completeness.
