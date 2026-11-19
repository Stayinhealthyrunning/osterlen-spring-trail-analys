# Österlen cleanup risk classification — 2026-10

Baseline: clean `origin/main` at `a54207726524a70d68102d79e8a0cb62d64438ed`.

| candidate group | class | evidence | action |
|---|---|---|---|
| `config/`, `data/`, `docs/` curated exports and foundation contracts | D | current foundation validation and Pages/frontend consumers | retain |
| archive/profile reports and `tools/*archive*` | D/E | source/provenance evidence and semantics audits; no age/name deletion basis | retain pending owner archival policy |
| `tools/sanitize_public_archives.py`, `privacy-registry.yml`, `guard-public-raw-sources.yml` | B/D | GDPR/public-source controls | retain unchanged |
| source discovery/probe/fetch workflows | D/E | active evidence collection and source coverage; many are read-only or artifact-producing | retain until each source contract is retired explicitly |
| route materialization/build/export workflows | D | foundation build and contract outputs | retain |
| `profile-archive-semantics.yml`, `profile-identity-fields.yml`, `profile-status-evidence.yml` | D/E | identity/semantics evidence; not disposable test noise | retain |

No tracked class-A file or class-C consolidation is proven safe. The 28-workflow
surface is source-discovery/validation-heavy and cannot be simplified by name or
age without changing evidence coverage. No deletion, raw-source publication,
GDPR change or visual/runtime change was made.
