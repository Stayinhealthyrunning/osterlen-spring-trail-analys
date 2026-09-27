# ÖST frontend delivery architecture and performance budget — 2026-09-27

## Decision

The large ÖST build should **not** load the full Engine 1.0 export at startup.

The measured full export contains all 9,871 results and is excellent as a canonical handoff/debug artifact, but its browser delivery shape should be:

1. **bootstrap.json** — event, race catalog, course metadata, capabilities/source version.
2. **one race JSON per race_key** — metadata, all result records, checkpoints, real splits and Duo team/member rows for exactly one selected edition.
3. **route/elevation bundle by course_version** — lazy-loaded only when a map/course/replay view needs it.
4. Future global history/person aggregates — purpose-built and on demand, never a reason to hydrate all race records at initial startup.

This gives us a simple two-stage normal navigation path rather than a complicated micro-shard architecture.

## Real measured baseline

Source: `reports/engine-payload-profile.json`, generated from the complete frozen/curated Engine 1.0 export.

| Payload | Raw | gzip -9 |
|---|---:|---:|
| Full Engine 1.0 export | 5,417,501 B / 5.2 MiB | 450,548 B / 440.0 KiB |
| Bootstrap candidate | 27,041 B / 26.4 KiB | 1,980 B / 1.9 KiB |
| Largest selected race | 329,072 B / 321.4 KiB raw maximum | 29,138 B / 28.5 KiB gzip maximum |
| Bootstrap + largest selected race | — | about 30.4 KiB |
| Bootstrap + median selected race | — | about 15.1 KiB |

The full payload compresses extremely well, but parsing 5.2 MiB of JSON and constructing objects for every race at startup has no user benefit when a visitor normally views one edition at a time.

## Where the full payload lives

Measured top-level contribution:

| Section | Raw | gzip |
|---|---:|---:|
| races | 3.7 MiB | 338.8 KiB |
| splits | 1.2 MiB | 83.1 KiB |
| team_members | 170.4 KiB | 9.5 KiB |
| teams | 35.9 KiB | 4.8 KiB |
| race_catalog | 22.9 KiB | 1.2 KiB |
| checkpoints | 17.8 KiB | 648 B |
| courses | 3.1 KiB | 625 B |

The browser therefore gains almost everything by withholding **records and splits for unselected races**. Course/catalog metadata is tiny and belongs in bootstrap.

## Why one shard per race is enough

We explicitly considered splitting records, splits and Duo data into separate files. Current measurements do not justify it.

Even the heaviest edition, Ultra 2025, is only about **28.5 KiB gzip** as a complete selected-race bundle. Splitting that into multiple requests would add request/cache/state complexity for negligible transfer savings.

Therefore:

- finish-only Trail editions: one race request;
- Ultra: one race request containing records + real splits;
- Duo: one race request containing team records + real splits + team/member rows;
- no per-runner network requests;
- no separate split request unless future datasets grow enough to break the budget.

## Route and elevation

Route/elevation assets remain deliberately separate from race result data.

Reasons:

- many result views do not need a map;
- historical editions may have course identity without a redistributable local route asset;
- Trail 13/14 currently has a recipe-only provisional reference and must not leak into runtime as an authoritative GPX;
- replay/map code itself should be lazy-loaded;
- route/elevation bundles have different cache invalidation semantics from result data.

Cache route assets by `course_version`, not marketing distance.

## Performance budget

Machine-readable source: `config/frontend-performance-budget.json`.

Current hard data budgets:

- bootstrap: **≤ 10 KiB gzip**;
- selected race: **≤ 75 KiB gzip** and **≤ 600 KiB raw**;
- bootstrap + selected race: **≤ 100 KiB gzip**;
- full Engine export regression ceiling: **≤ 750 KiB gzip**.

Measured current values have substantial headroom:

- bootstrap uses ~19% of its hard gzip ceiling;
- largest race uses ~38% of its hard gzip ceiling;
- bootstrap + largest race uses ~30% of its hard ceiling.

The full export may grow without directly hurting initial navigation, but its regression ceiling catches accidental field duplication or runaway payload growth.

## Provisional frontend-code budgets

These become CI gates when real frontend artifacts exist:

- initial JS: **≤ 256 KiB gzip**;
- initial CSS: **≤ 75 KiB gzip**;
- initial HTML: **≤ 32 KiB gzip**;
- critical initial transfer, excluding images/maps/routes/non-selected race data: **≤ 512 KiB gzip**.

These limits are intentionally compatible with the current reference implementations while still forcing the ÖST build to use progressive loading.

For context, current raw application JavaScript in the reference repos is approximately:

- Gotaleden app modules: **394 kB raw**, plus Leaflet ~148 kB raw;
- Ultravasan app modules: **509 kB raw**, plus Leaflet ~148 kB raw.

The large Ultravasan data scripts are not a pattern to copy into initial load. ÖST's measured sharding makes that unnecessary.

## Build artifact contract

`tools/build_engine_delivery_shards.py` creates:

```
out/engine-data/
  bootstrap.json
  manifest.json
  races/
    ost-2018-trail14.json
    ...
    ost-2026-ultra60.json
```

The builder:

- regenerates the canonical Engine 1.0 payload from the curated database;
- preserves one common payload SHA-256 in bootstrap and every race shard;
- verifies exactly 34 race instances;
- verifies exactly 9,871 result rows, 6,123 splits, 300 Duo teams and 599 team-member rows;
- enforces the data budgets;
- does not emit the monolithic Engine JSON into the browser delivery directory;
- does not embed route/elevation geometry in race shards.

## Startup sequence

Recommended app boot:

1. load HTML/CSS/critical JS;
2. fetch `bootstrap.json`;
3. resolve requested/default `race_key`;
4. fetch that single race shard;
5. render result/finish functionality immediately;
6. only when a route-dependent view is opened:
   - load map/replay modules if not already loaded,
   - fetch approved route/elevation bundle for that course_version.

Changing year/race should fetch only the new race shard and reuse bootstrap/cached course assets.

## History views

Cross-year race history should not force all full race shards into memory.

Use purpose-built aggregates for:
- annual participation counts,
- course-version records,
- distributions already derivable offline.

Personal repeat-runner history remains deferred until a confidence-bearing identity linkage exists. When implemented, it should have its own compact history index rather than using name scans across all race JSON files in the browser.

## What must still be measured during frontend implementation

Data transport is now measured. The following require the actual browser app:

- JSON parse and render time on representative mobile hardware;
- FCP/LCP/INP;
- memory after repeated race switching;
- map/replay frame rate and peak memory;
- actual HTTP gzip/Brotli behavior on the production hosting path;
- real built JS/CSS gzip sizes.

Those measurements should tune budgets downward where practical, not be used as a reason to abandon progressive loading.

## Conclusion

The data layer is **not a performance risk** if we use the measured architecture.

A normal first race view needs roughly **15–30 KiB of gzip-compressed race+bootstrap data**, versus 440 KiB for the complete Engine export and 5.2 MiB after decompression. The simplest correct architecture is therefore bootstrap + one complete selected-race shard, with maps/routes/history loaded on demand.
