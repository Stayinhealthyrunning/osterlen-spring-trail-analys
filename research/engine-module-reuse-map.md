# ÖST – Engine 1.0 module reuse map

## Purpose

This file is the concrete implementation map for the large ÖST Analys build. It identifies which proven modules/patterns should be reused from the two reference implementations and where ÖST-specific logic must remain local.

Canonical semantic contract:

- Repository: `Stayinhealthyrunning/gotaleden-splits`
- Contract: `config/engine-contract-v1.json`
- Contract ID: `loppanalys-engine-1.0`
- Status: frozen

Primary ÖST source-side handoff:

- `data/derived/ost-analysis-2018-2026.sqlite.gz`
- `config/engine-adapter.json`
- `config/course-versions.json`
- `reports/engine-readiness.json`

## Reuse strategy

| Build concern | Primary reference | Useful reference files/modules | ÖST rule |
|---|---|---|---|
| Engine semantic boundary | Gotaleden | `config/engine-contract-v1.json` | Do not invent an ÖST-specific parallel contract. |
| Runtime normalized model | Gotaleden | `docs/assets/data-adapter.js` | Feed Engine 1.0 export; keep missing source fields null. |
| App/race selection state | Gotaleden | `docs/assets/app-state.js`, `race-ui.js` | State must be event/race-edition scoped, not hard-coded to Ultra. |
| Capability-driven UI | Gotaleden | Engine contract + data adapter | Use ÖST per-edition capabilities from `reports/engine-readiness.json`; hide unsupported modules. |
| Progressive loading | Ultravasan | `docs/assets/data-loader.js`, `data-index.js` | Prefer shell → active race → core → full hydration for the 9,871-result dataset. |
| Race/edition contracts | Ultravasan + Gotaleden | `docs/assets/race-contracts.js`, Engine 1.0 race contract | Participant entity and competition/team structure must be explicit. |
| Results/search/profile | Gotaleden | `data-adapter.js`, profile/personal-summary modules | Support all finish/result-capable editions, including finish-only short races. |
| Distribution/statistics | Gotaleden | `charts.js`, distribution helpers in `data-adapter.js` | Preserve small-sample guards and source-backed filters. |
| Segment/pacing analysis | Gotaleden | `interactive-analysis.js`, segment helpers in `data-adapter.js` | Only Ultra/Duo editions with observed intermediate splits get segment analysis. |
| Map/replay | Gotaleden | `map-engine.js`, `runner-replay.js`, `map-duel.js`, `playback.js` | Initial enablement only where ÖST readiness says replay=true; currently Ultra/Duo 2024–2026. |
| Course/elevation analysis | Gotaleden + Ultravasan | Gotaleden `course-difficulty.js`; Ultravasan `course-intelligence.js` | Route bundles keyed by course_version; use common elevation policy, never raw-GPX D+ as cross-year truth. |
| Whole-course history | Gotaleden + Ultravasan | Gotaleden `history-engine.js`; Ultravasan `history-intelligence.js` | Compare exact course_version or explicit compatibility group only. |
| Person history / repeat runners | Ultravasan | verified identity/history patterns | Keep disabled in ÖST until separate confidence-bearing identity linkage exists. |
| Relay/team presentation | Gotaleden | relay/team contract/tests | Duo participant.entity=team; keep source_sequence; never infer leg_no. |
| Favorites/shareable state | Gotaleden | `favorites.js`, app state patterns | Event/race keys must be namespaced to ÖST and version-safe. |
| Method/help content | Gotaleden | `analysis-help.js`, `analysis-help-content.js` | Explain missing capabilities and provisional route provenance explicitly. |
| Frontend styling/layout | Gotaleden as base, Ultravasan selectively | `docs/index.html`, style assets | Reuse structure, not event-specific branding/content. |
| Advanced historical intelligence | Ultravasan | `history-intelligence.js`, `audience-analytics.js` | Introduce only after base Engine 1.0 parity and data-evidence tests pass. |

## ÖST-specific logic that must stay local

The following must **not** be moved into generic frontend assumptions:

1. Sportstiming source acquisition and parsing.
2. Frozen/raw source provenance and audits.
3. ÖST race-family/year catalogue.
4. Checkpoint normalization, including the 2022–2023 `32 km` vs `Bengtemölla` distinction.
5. Duo source semantics and unresolved member-to-leg assignment.
6. Course-version decisions and route provenance.
7. Trail 13/14 provisional Hallamölla-splice evidence.
8. Trail 5 reconstructed-route provenance.
9. Historical demographic coverage gaps.
10. Future cross-year identity linkage evidence.

## Recommended implementation order

### Phase A — payload and shell

1. Run the reproducible Engine 1.0 handoff export.
2. Load event + race catalog + course metadata.
3. Implement race selector/year selector and capability-aware navigation.
4. Verify cancelled years 2020/2021 are explicit and never appear as missing result years.

Acceptance:
- all 34 held race instances load;
- 9,871 result rows remain count-stable;
- unsupported tabs/modules are hidden or factually explained.

### Phase B — finish/result analysis

Implement for all race families:
- searchable results;
- finisher/DNF counts;
- placement and finish-time distributions;
- runner/team profile;
- club/country views where source coverage exists;
- sex/age views only where source-backed coverage exists.

Acceptance:
- 2018/2019/2023 demographic gaps remain null rather than inferred;
- Trail races work correctly despite having no intermediate splits.

### Phase C — Ultra/Duo split analysis

Implement:
- timing checkpoints;
- segment pace/placement;
- Duo team profiles;
- Bengtemölla analysis semantics.

Acceptance:
- 2022/2023 `32 km` and `Bengtemölla` remain distinct source observations;
- Duo source_sequence is visible/preserved;
- no guessed leg assignment.

### Phase D — route, replay and map

Initial route/replay scope:
- Ultra 2024
- Duo 2024
- Ultra 2025
- Duo 2025
- Ultra 2026
- Duo 2026

Do not unlock replay for an edition merely because another edition in the same family has a route.

Trail 5 may have a reconstructed local geometry asset for route display/methodology where explicitly labelled, but no replay is possible without real intermediate timing anchors.

Trail 13/14 provisional 13.472 km recipe must **not** be exported as an official/local route asset.

### Phase E — course history

Enable:
- exact course-version records;
- explicit comparison-group history;
- participation history across years independently of route comparability.

Do not mix finish-time records across materially different course versions as if they were one record table.

### Phase F — identity/history intelligence

Only after a dedicated linkage layer exists:
- repeat runners;
- personal multi-year history;
- veteran/most-improved type views.

Required identity output must carry:
- person_key,
- confidence/status,
- evidence basis,
- ambiguity handling.

Name equality alone is insufficient.

## First-build acceptance matrix

| Test case | Must work | Must stay disabled/qualified |
|---|---|---|
| Ultra 2018 | result + historical split analysis | replay/map route interpolation |
| Ultra 2023 | result + splits; separate 32 km/Bengtemölla observations | route replay without local approved asset |
| Ultra 2025 | full result + split + replay/map | — |
| Duo 2025 | team result + splits + members + replay/map | member→leg inference |
| Trail 22 2026 | finish/result + course-version context | split/replay |
| Trail 14 2026 | finish/result + provisional course methodology | official GPX claim, replay |
| Trail 5 2026 | finish/result + explicitly reconstructed route context | replay without splits |
| Trail 22 2018 | finish/result | assigned course version until provenance resolved |

## Performance and loading guidance

The curated data volume is moderate but large enough that the frontend should avoid eagerly constructing every profile/chart for all years at startup. Follow Ultravasan's progressive-loading pattern:

1. lightweight app shell and race catalog,
2. selected race records,
3. selected race splits/team structures,
4. route/elevation bundle only when required,
5. broader history datasets on demand.

Caching should be keyed by:
- event_key,
- race_key,
- course_version,
- filter state.

Do not cache derived results solely by marketing distance or race-family label.

## Build-start command sequence

Before implementing frontend code:

```bash
python tools/validate_foundation.py
python tools/build_engine_readiness_report.py
python tools/validate_prebuild_readiness.py
python tools/export_engine_v1.py --output out/ost-engine-v1.json
```

Or use the manual GitHub workflow:

`.github/workflows/export-engine-v1.yml`

The exported payload is the integration boundary. Acquisition scripts should not be invoked as part of normal frontend development.
