# Tooling map

The `tools/` directory contains **build/validation code plus source-maintenance and research utilities**. None of these Python scripts are shipped to the browser.

## Active large-build path

These are the scripts expected to matter directly when the ÖST analysis tool is built:

- `build_engine_readiness_report.py`
- `export_engine_v1.py`
- `profile_engine_payload.py` — measures the real complete Engine export and section/race sizes
- `export_engine_web_bundle.py` — builds bootstrap + one browser JSON bundle per race
- `validate_frontend_performance_budget.py` — enforces measured data-delivery budgets
- `validate_foundation.py`
- `validate_prebuild_readiness.py`
- `audit_repository_hygiene.py`
- `build_curated_analysis_db.py` — only when normalization/source semantics change, not for route-only changes
- `build_route_elevation_evidence.py` — when elevation evidence/policy is refreshed

## Frozen-source maintenance

These scripts are retained because they reproduce or audit the source layer, but they are **not normal frontend-development steps**:

- Sportstiming fetch/normalize/freeze/audit/profile scripts
- source coverage/catalog builders
- organizer/Trace de Trail source discovery and GPX analysis
- Duo evidence and Bengtemölla evidence tools

The full Sportstiming refreeze workflow is manual-only. Do not rerun it merely to develop the frontend.

## Route-reconstruction research

Raster/OSM reconstruction helpers remain for provenance and future GPX validation. They are not part of Engine 1.0 runtime code. The current route truth is always `config/course-versions.json`.

The former Trail 13/14 14.249 km raster route is superseded. Its active-looking GPX/GeoJSON/candidate files have been removed from `routes/ost/trail14-current-reference/`; only QA/provenance metadata remains, and the historical bytes remain recoverable from Git history.

## Rule

Do not optimize repository size by deleting reproducibility/provenance tools unless they are truly obsolete. They are tiny compared with the frozen data and do not affect browser performance. Optimize the **deployed frontend payload and execution path**, not the existence of offline maintenance scripts.
