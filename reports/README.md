# Reports

Generated validation, source, geometry and engine-readiness reports live here. Reports are derived artifacts; source truth remains in the frozen archive and curated database contracts.

## Start here

- `result-archive-summary.json` – frozen Sportstiming archive counts, hashes and coverage.
- `result-archive-audit.json` / `.md` – deep consistency audit of the frozen archive. A valid foundation requires verdict `PASS`.
- `curated-analysis-db-summary.json` / `.md` – counts, hashes and integrity checks for `data/derived/ost-analysis-2018-2026.sqlite.gz`.
- `engine-readiness.json` / `.md` – current race-by-race feature and field availability used for generic-engine gating.

## Data semantics / quality

- `status-evidence-profile.json` / `.md` – explicit frozen-source evidence used to resolve DNF while leaving unsupported status as UNKNOWN.
- `identity-field-profile.json` / `.md` – aggregate offline inventory of recoverable Sportstiming list/detail fields; no participant names are emitted by this report.
- `archive-semantics-profile.json` / `.md` – status and Duo table/structure inventory.
- `duo-member-evidence.json` / `.md` – aggregate evidence around Duo member rows and why `leg_no` remains unassigned.
- `bengtemolla-double-timing.json` / `.md` – analysis of the separate 32 km and Bengtemölla observations.

## Course / source coverage

- `source-coverage.json` / `.md` – source coverage by race family/year.
- `tracedetrail-public-geometry-analysis.json` / `.md` – derived public geometry comparison without republishing third-party route coordinate series.
- `gpx-analysis.json` / `.md` – local GPX diagnostics.
- `wayback-asset-inventory.json` / `.md` – historical archived-asset discovery diagnostics.

## Canonical relationship

`data/archive/ost-results-2018-2026.sqlite.gz`
→ immutable provenance/source archive
→ `data/derived/ost-analysis-2018-2026.sqlite.gz`
→ curated engine handoff
→ `engine-readiness.json`
→ runtime feature gating.
