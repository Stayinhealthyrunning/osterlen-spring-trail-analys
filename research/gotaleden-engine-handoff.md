# ÖST → Loppanalys Engine 1.0 handoff

## Purpose

This repository owns Österlen Spring Trail source acquisition, provenance, normalization, course-history decisions and the completed source-side analysis database. Frontend integration now targets the frozen semantic contract **Loppanalys Engine 1.0** rather than one product repository.

The machine-readable ÖST mapping is `config/engine-adapter.json`.

Reference implementations:

- Gotaleden: event, competition, participant and capability contracts; future-edition portability.
- Ultravasan: progressive data loading, route evidence, identity/history and later analysis modules.

## Start here — source-side work is already complete

Do **not** recrawl Sportstiming to begin engine integration.

Primary engine input: `data/derived/ost-analysis-2018-2026.sqlite.gz`.

Immutable provenance archive: `data/archive/ost-results-2018-2026.sqlite.gz`.

The curated database contains 34 held race-year instances, 9 871 results, 9 571 individual participant rows, 300 Duo teams, 599 published Duo member rows, 6 123 observed split passages and 699 derived metrics. `reports/engine-readiness.json` is the runtime-facing evidence for feature availability.

## Engine 1.0 boundary

ÖST must emit the semantic concepts:

- event
- race_catalog
- courses
- races
- checkpoints
- splits
- optional teams/team_members
- explicit participant + competition semantics
- per-edition capabilities
- route/elevation bundles keyed by course_version when a usable local asset exists

Source acquisition, provider parsing and provenance remain ÖST-specific.

## Critical ÖST constraints

### Race family is not geometry

A RaceEdition receives a `course_version` only from verified evidence in `config/course-versions.json`. Family membership alone never enables whole-course performance comparison.

### Sparse timing is valid

Ultra has real intermediate timing in supported years. The imported public archive did not expose intermediate split tables for Trail 21/22, Trail 13/14 or Trail 5. Finish-only races remain valid Engine 1.0 races; segment/replay features remain disabled rather than synthesized.

### Bengtemölla 2022–2023

`32 km` and `Bengtemölla` remain separate published observations. The derived interval may be described as a between-observation/service-window candidate, never as verified stationary aid-station time.

### Duo

Duo uses the same-year Ultra route/course version. Team results, real team splits and 599 published member rows are source-backed. `source_sequence` is retained; `leg_no` remains NULL because the available evidence does not prove member-to-leg assignment.

Engine mapping is therefore:

- participant.entity = team
- competition.format = duo
- team_structure.kind = sequential
- team_structure.leg_count = 2
- team_structure.member_assignment = unknown

### Demographic gaps

Exact age/sex are used only where published. Historical missing fields stay missing. No inference from names and no exact age inferred from an age band.

## Route-data policy

Geometry evidence for comparability and a redistributable/local route asset are different things. Replay/map requires a locally usable route asset plus real timing anchors. Current evidence makes Ultra/Duo 2024–2026 replay/map-ready; older split-capable years remain route-blocked until a suitable local asset exists. Trail 13/14 currently has only a **provisional 13.472 km Hallamölla-splice recipe** based on Trail 21/22 2022–2024 public geometry. It may support methodology/course discussion but must not be exposed as an official or redistributable route asset until an authentic/approved GPX is secured.

## Capability gating

`reports/engine-readiness.json` controls feature availability per RaceEdition. The frontend must hide unavailable features or explain the limitation. It must never borrow capability from another year/family.

Current evidence:

- 34 held race-year instances with results,
- 13 with real split analysis data,
- 6 with splits + local route data sufficient for replay/map,
- 19 with verified course version.

## Integration sequence

1. Validate the curated database against Engine 1.0 semantics.
2. Build an ÖST adapter that emits the Engine 1.0 payload without recrawling sources.
3. Materialize participant/competition/capabilities per RaceEdition.
4. Build route bundles only for course versions with usable local assets.
5. Map checkpoints through `config/checkpoint-normalization.json`, retaining source labels.
6. Acceptance-test 2018 Ultra, 2023 Ultra, 2025 Ultra, 2026 Trail22 and at least one Duo year.
7. Add cross-year person views only when a separate confidence-bearing identity layer passes its own tests.

## Acceptance rule

Correct absence is a feature. A finish-only Trail race with no replay is more correct than a visually complete page built from invented checkpoints or borrowed geometry.
