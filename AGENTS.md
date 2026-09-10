# AGENTS.md – Österlen Spring Trail Analys

## Scope
- Analysis starts in 2018.
- Held editions: 2018, 2019, 2022, 2023, 2024, 2025, 2026.
- 2020 and 2021 are CANCELLED, never treated as missing result years.
- Race families: ultra60, duo60, trail22, trail14, trail5.

## Source-of-truth rules
- Sportstiming is the official result source of record.
- Preserve raw source fields before normalization.
- Never fabricate splits, checkpoint passages, ranks, DNS/DNF status, relay membership or course geometry.
- Missing source observations remain missing.
- Third-party race databases may be used for cross-checking only, not to overwrite official timing data.

## Course rules
- Marketing labels (60 km, 21/22 km, 13/14 km) are not proof of identical geometry.
- `course_version` stays unassigned until GPX comparison verifies equivalence.
- Duo uses the matching year's Ultra 60 route; only competition structure/exchange point differs.
- Race-day marking may differ from published GPX. Preserve this limitation in public methodology.

## Repository strategy
- Do not copy the current Gotaleden frontend/core wholesale while its generic refactor is still in progress.
- Keep ÖST-specific source data, manifests and research independent.
- When the generic Gotaleden core is ready, integrate it through event configuration/adapters rather than forking hard-coded race logic.

## Provenance
Every downloaded source asset must have:
- source URL
- source type
- verification status
- intended target filename
- SHA-256 checksum after download
- notes on redistribution/provenance when relevant
