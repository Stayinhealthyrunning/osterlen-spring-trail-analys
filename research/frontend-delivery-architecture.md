# Frontend delivery architecture and performance budget

## Decision

The large ÖST build shall **not** load the complete Engine 1.0 payload at startup.

Measured on 2026-09-27 from the real curated dataset:

- Full Engine 1.0 JSON: **5,417,501 bytes raw / 450,548 bytes gzip**.
- Metadata-only bootstrap prototype: **31,084 bytes raw / 2,633 bytes gzip**.
- Largest selected race bundle: about **29 KB gzip**.
- Bootstrap + largest selected race: about **31.8 KB gzip**.
- The full payload contains 9,871 results, 6,123 splits, 300 teams and 599 team-member rows.

Although 450 KB gzip is not an extreme network transfer, parsing and retaining about 5.2 MiB of JSON plus all derived UI state for every race/year is unnecessary. The measured sharded alternative is substantially smaller and gives a cleaner runtime model.

## Delivery model

Use three layers:

1. **Bootstrap/index**
   - event metadata
   - race catalogue
   - course metadata
   - capability metadata
   - small race summaries/counts
   - source/version labels

2. **Selected race-edition bundle**
   - selected race metadata
   - all result records for that race/year
   - checkpoints
   - observed splits
   - team/member rows where relevant

3. **Lazy course assets**
   - route geometry
   - elevation profile
   - map/replay-specific data
   - loaded only when the selected race/capability requires them

The delivery exporter is `tools/export_engine_delivery.py`. It writes `index.json`, one `races/<race_key>.json` file per race edition, and a manifest with hashes and measured raw/gzip sizes.

## Enforced data budgets

The machine-readable budget is `config/performance-budget.json`.

Current limits:

- bootstrap: **<= 8 KiB gzip**, **<= 96 KiB raw**
- one selected race: **<= 48 KiB gzip**, **<= 512 KiB raw**
- bootstrap + largest selected race: **<= 64 KiB gzip**
- full canonical Engine payload sanity ceiling: **<= 768 KiB gzip**

These limits deliberately contain headroom over the measured data and are checked by `tools/validate_performance_budget.py`.

## Provisional frontend budgets

These become enforceable once the real frontend exists:

- initial HTML + CSS + JavaScript: **<= 300 KiB gzip**
- initial code + Engine data: **<= 384 KiB gzip**
- one lazy route/elevation bundle: **<= 300 KiB gzip**

Images/fonts and optional map tiles are measured separately because their loading policy differs.

## Loading rules

- Never open SQLite in the browser.
- Never expose `data/archive/`, raw Sportstiming snapshots, research reports or Python tooling to the public runtime.
- Do not load all 34 race editions to render a single selected race.
- Switching race/year loads only the requested race shard.
- Route/elevation data are keyed by `course_version` and cached separately.
- Replay/map libraries should be lazy-loaded when their UI is opened.
- Cross-year charts should use compact precomputed aggregates where possible; richer history can load explicit additional shards on demand.
- Cache keys must include event/race/course version so route or course changes cannot reuse stale derived data.

## Why not use the monolith?

The monolith compresses unusually well because result records are repetitive. That makes the network number look small, but the browser would still need to parse the full **5.2 MiB raw JSON** and retain thousands of records that are irrelevant to the current view.

The sharded model reduces first meaningful Engine data from roughly **440 KiB gzip** to roughly **15-32 KiB gzip**, depending on selected race, while retaining exactly the same canonical Engine semantics.

## Performance work during implementation

When the real frontend is available, CI should additionally measure:

- initial JS/CSS gzip and brotli sizes
- first-contentful and interaction-ready timings on a representative mobile device
- JSON parse time for the largest race shard
- chart construction time for the largest Trail and Ultra fields
- route/elevation decoding and map memory
- replay memory and animation frame stability
- cache behavior when switching between years

Any budget increase should be an explicit reviewed decision with measured justification, not silent payload growth.
