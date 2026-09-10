# AGENTS.md – Österlen Spring Trail Analys

## Project state
This repository is a **handoff-ready ÖST foundation**. Source discovery, race/year modelling, Sportstiming schema inventory, checkpoint normalization, course-version evidence, source-coverage logic and the contract toward the future generic Gotaleden-derived engine are already prepared.

Do **not** restart the discovery phase. Read `config/foundation-state.json`, `PREP_STATUS.md` and `research/gotaleden-engine-handoff.md` before implementing the frontend or production import pipeline.

## Scope
- Analysis starts in 2018.
- Held editions: 2018, 2019, 2022, 2023, 2024, 2025, 2026.
- 2020 and 2021 are CANCELLED, never treated as missing result years.
- Race families: `ultra60`, `duo60`, `trail22`, `trail14`, `trail5`.

## Source-of-truth rules
- Sportstiming is the official result source of record.
- Preserve raw source fields/payloads before normalization.
- Never fabricate splits, checkpoint passages, ranks, DNS/DNF status, relay membership or course geometry.
- Missing source observations remain missing.
- A sampled participant detail page proves that a split schema exists; it does not prove complete split coverage for every participant.
- Third-party race databases may be used for cross-checking only, not to overwrite official timing data.

## Course rules
- Marketing labels (60 km, 21/22 km, 13/14 km) are not proof of identical geometry.
- `config/course-versions.json` is the authoritative current course-version model.
- Exact public-geometry fingerprints may establish identical course versions; strongly overlapping but non-identical routes remain separate versions and may share a comparison group.
- A verified course version does not imply that a redistributable/local GPX asset exists.
- Duo uses the matching year's Ultra 60 route; only competition structure/exchange semantics differ.
- Race-day marking may differ from published route geometry. Preserve this limitation in public methodology.

## Bengtemölla 2022–2023
Sportstiming exposes both `32 km` and `Bengtemölla`, only 0.1 km/100 m apart in the source schema. Aggregate samples show median elapsed gaps of 255 s (2022) and 142.5 s (2023), so these must **not** be collapsed as duplicate observations.

Working hypothesis: `32 km` is an approach/prewarning reading and `Bengtemölla` is recorded on departure after service. This is plausible but not physically verified. Use `Bengtemölla` as the canonical named checkpoint, preserve `32 km` separately, and label the derived gap only as a service-window candidate until timing-mat placement is independently confirmed.

## Repository strategy
- Do not copy the old/current Gotaleden frontend/core wholesale while the generic refactor is in progress.
- Keep ÖST-specific source data, manifests and research independent.
- When the generic Gotaleden core is ready, integrate it through `config/analysis-data-contract.json`, `config/engine-adapter.json` and the handoff notes rather than forking hard-coded race logic.
- Feature availability must be source-driven through the capability policy; never enable replay/map/pacing features merely because another race family has them.

## Provenance
Every downloaded source asset must retain:
- source URL
- source type
- verification status
- intended target filename
- SHA-256 checksum after download
- notes on redistribution/provenance when relevant

Trace de Trail public map geometry may be analyzed transiently for hashes, distances and cross-year corridor comparison. Do not automatically republish its full coordinate arrays or treat login-protected GPX export as an approved redistributable asset.

## Validation
Run:

```bash
python tools/validate_foundation.py
```

before merging structural changes. The `Validate ÖST foundation` GitHub Action runs the same consistency checks automatically.
