# ÖST → generalized Gotaleden engine handoff

## Purpose

This repository owns Österlen Spring Trail source discovery, provenance, normalization and course-history decisions. The generalized frontend/analysis engine being developed in `Stayinhealthyrunning/gotaleden-splits` should be reused after that refactor stabilizes rather than copied prematurely.

The machine-readable handoff contract is `config/engine-adapter.json`.

## What should remain ÖST-specific

- Sportstiming event/round discovery and result acquisition.
- Year/race-family catalogue from 2018 onward, including cancelled 2020/2021 editions.
- Sportstiming checkpoint-label normalization by year.
- Duo-specific source parsing and Bengtemölla exchange semantics.
- Trace de Trail/organizer route provenance and course-version evidence.
- Cross-year identity/linkage methodology.
- Source/capability matrix and all rules that prevent unsupported features from appearing.

## What should come from the generalized engine

The current Gotaleden frontend adapter already constructs races dynamically, indexes records/splits, supports multiple course assets keyed by course version, distinguishes analysis boundaries from replay anchors, interpolates replay only between real timing passages and gates whole-course comparison by course version/comparison group. Those concepts match ÖST well and should not be reimplemented here.

Expected frontend payload concepts are:

- `race_catalog`
- `courses`
- `races`
- `checkpoints`
- `teams`
- `splits`
- route/elevation bundles keyed by `course_version`

See `config/engine-adapter.json` for field-level expectations.

## Critical ÖST differences the engine must tolerate

### Multiple years and changing course geometry

A marketing family such as `ultra60` spans several genuinely different or not-yet-proven-equivalent geometries. `race_family` therefore never implies route comparability. A race instance gets a `course_version` only from `config/course-versions.json`.

Same course version → exact/verified same geometry for whole-course comparison.
A shared `whole_course_comparison_group`, if later introduced → compatible whole-course comparison with explicit methodology.
No shared version/group → do not compare records/whole-course pace as if the courses were identical.

### Sparse checkpoint layouts

Ultra has published intermediate timing, but the layout changes by era:

- 2018–2019: Stenshuvud, Bengtemölla, Vantalängan, finish.
- 2022–2023: `32 km`, `Bengtemölla`, finish.
- 2024–2026: `34 km`, finish; route evidence maps 34 km to Bengtemölla.

Shorter races currently have finish/detail results but sampled detail pages do not expose comparable intermediate split tables. The generic UI therefore needs to work perfectly well with zero intermediate splits.

### Bengtemölla 2022–2023

Do not collapse `32 km` and `Bengtemölla` into one raw observation. Sportstiming reports them as consecutive readings only 0.1 km apart, while sampled elapsed gaps are far too long and variable to represent ordinary 100 m running time.

Working interpretation (not physically verified):

- `32 km` = approach/prewarning candidate.
- `Bengtemölla` = canonical named checkpoint, plausibly an exit reading after aid-station service.
- Difference = `bengtemolla_service_window_seconds`, exposed only with wording that it is a candidate service window rather than confirmed stationary dwell time.

The primary analysis boundary may use Bengtemölla while the earlier reading remains a replay/source timing observation if appropriate.

### Duo

Duo uses the same full route as the same-year Ultra and exchanges at Bengtemölla. Do not model it as two hardcoded 30.000 km legs. The exchange distance should come from the relevant route/checkpoint projection.

Sportstiming’s Duo list does not currently expose the same individual result-link structure as the individual classes, so a dedicated relay/team adapter is being investigated. Until verified, do not synthesize member/leg data.

## Route-data policy

There are two distinct concepts:

1. **Geometry evidence for historical comparability.** Public Trace de Trail map pages expose geometry required to render the public route. We may decode it transiently, compute fingerprints/overlap/course-version evidence, and store derived diagnostics.
2. **Route asset distributed with the site.** A frontend map/replay needs a locally usable route asset. Do not equate a public-geometry fingerprint with permission/availability to redistribute the full coordinate sequence. Organizer-direct/user-provided/local GPX assets remain the preferred site assets.

This distinction lets us establish that two historical years are geometrically equivalent without silently rebuilding and publishing an authenticated GPX export.

## Elevation policy

Never compare raw accumulated D+ from heterogeneous providers/methods. Route/elevation bundles should be processed with one common method. The user-provided 2025 Suunto barometric activity is an independent race-day reference for elevation-profile shape; it is not a universal official D+ truth and its dense raw point-to-point vertical sum must not be used.

## Capability gating

`data/derived/analysis-capabilities.json` is the source of truth for whether an analysis has the evidence it needs. Typical states:

- `source_ready`: required source evidence observed; production UI/import can be implemented.
- `adapter_needed`: source exists but format-specific parsing remains.
- `blocked_pending_source`: required source evidence is absent/not recovered.
- `blocked_pending_geometry`: results exist but route/course-version evidence or usable route asset is missing.
- `not_available_in_sample`: sampled public result did not expose the source structure; do not manufacture it.

UI rule: hide unavailable functions or show a short factual explanation. Never fill an empty chart by inference.

## Recommended integration sequence after Gotaleden core stabilizes

1. Freeze the generic engine contract/version in Gotaleden.
2. Generate `data/derived/race-catalog-enriched.json` and the final normalized ÖST result/split payload.
3. Build course bundles only for course versions with usable route assets.
4. Map ÖST result/checkpoint fields into the engine contract without changing source semantics.
5. Run generic engine tests against at least: 2018 Ultra, 2023 Ultra (double Bengtemölla timing), 2025 Ultra, 2026 Trail22 (no intermediate split), and one Duo year.
6. Enable features from the capability matrix rather than by hardcoded race-family checks.
7. Add cross-year views only after course-version and repeat-runner identity rules are tested.

## Acceptance criteria for the handoff

The ÖST integration is ready when:

- every held race/year has a stable `race_key` and Sportstiming round binding;
- every emitted participant/team record has traceable source provenance;
- no emitted split lacks a published timing observation;
- checkpoints have explicit source label plus semantic key;
- every map/replay-enabled race has a usable local route asset;
- cross-year whole-course comparisons respect course versions;
- Duo member/leg structure is source-backed;
- short-distance races remain useful even with finish-only timing;
- 2020/2021 are represented as cancelled years, not missing data;
- tests include sparse splits, changed checkpoint names, missing geometry and relay data.
