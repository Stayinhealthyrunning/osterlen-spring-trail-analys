# Repository hygiene audit — 2026-09-27

## Conclusion

The repository is **not bloated in a way that can make the future browser application slow**. The current tracked working tree is about **20.3 MB** across **274 files**. Almost all weight is intentional source/provenance data, not executable application code.

Current size profile before this cleanup pass:

| Area | Size | Interpretation |
|---|---:|---|
| `data/` | 17.85 MB | source/provenance + frozen/curated data |
| `reports/` | 1.51 MB | generated diagnostics/audit evidence |
| `tools/` | 0.37 MB | 60 Python maintenance/research scripts |
| `.github/workflows/` | 0.05 MB | 26 automation workflows |
| `route_engine/` | 0.04 MB | route-research engine/provenance |
| `routes/` | 0.24 MB | reconstructed/reference route artifacts |
| `docs/` | <1 KB | current placeholder only |

The two intentional compressed SQLite files alone account for about **12.35 MB**:
- `data/archive/ost-results-2018-2026.sqlite.gz`
- `data/derived/ost-analysis-2018-2026.sqlite.gz`

The Christinehof OSM research extract accounts for another **2.20 MB**. Python tooling is only about **0.37 MB**, so deleting research scripts would have essentially no effect on frontend load time.

## What was optimized

1. **Frozen source archive is now manual-only to rebuild.** Normal config/frontend work can no longer accidentally trigger a full Sportstiming refetch.
2. **Course-version-only changes no longer rebuild the curated SQLite database.** Course decisions are overlaid at readiness/export time as intended.
3. **Heavy source-report automation no longer watches all of `config/**`.** Only source-relevant config changes can trigger it.
4. **Validation automatically discovers all unit tests** instead of maintaining a hand-written test list.
5. **All Python tooling is syntax-compiled in CI.**
6. **Transient build/test directories are ignored** (`out/`, `node_modules/`, pytest/ruff/mypy caches, `dist/`, coverage artifacts).
7. **A repository-hygiene CI guard** rejects tracked transient artifacts and prevents raw SQLite/OSM files from leaking into the future `docs/` web surface.
8. **Four completed short-course research workflows were removed from `main`** so they no longer clutter the Actions surface or suggest that route reconstruction is part of the production build.
9. **Superseded Trail 13/14 GPX/GeoJSON/candidate files were removed from the active route directory.** QA/provenance remains, and exact historical bytes are recoverable from Git history.
10. **The route-engine prototype was explicitly marked research-only and stale Trail 13/14/Trail 5 examples were brought into line with the current route policy.**

## What is intentionally retained

Not every historical/research file is "active application code". Some files are retained because they provide reproducibility or provenance:

- frozen source database and audit data;
- organizer GPX/maps;
- OSM/raster material used in short-course reconstruction;
- superseded Trail 13/14 reconstruction evidence;
- source-discovery reports;
- source acquisition/research scripts.

These files do **not** execute in the browser and do not make the analysis site slower. Deleting them would mainly reduce repository checkout size while losing useful auditability.

## Runtime rule for the large build

The future website must not load or copy the repository wholesale. Runtime assets must be built explicitly from:

- the Engine 1.0 payload,
- approved course/route bundles,
- frontend JavaScript/CSS/media actually used by the UI.

Raw `data/archive/`, `data/source/`, `reports/`, `tools/` and research-only route material must stay outside the deployed frontend unless a specific asset is deliberately promoted.

## Remaining optimization work

Frontend performance cannot be fully optimized before the frontend exists. During the large build, measure and enforce:

- compressed Engine payload size,
- initial JavaScript/CSS transfer size,
- progressive loading by selected race/year,
- route/elevation lazy loading,
- no eager construction of all 9,871 profiles/charts,
- browser cache keys scoped by event/race/course version,
- mobile performance and map/replay memory use.

The prebuild repository is therefore lean enough to start. The next meaningful performance work belongs to the generated Engine payload and browser runtime, not to deleting provenance scripts.
