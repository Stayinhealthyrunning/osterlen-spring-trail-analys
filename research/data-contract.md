# ÖST staging data contract

This document defines the source/staging layer that should be ready before the generalized Gotaleden analysis core is integrated.

## Compatibility target

`tools/schema_compat_gotaleden.sql` is a snapshot of the current Gotaleden relational contract as of 2026-09-10. It is intentionally named `schema_compat_gotaleden.sql`, not `schema.sql`, because Gotaleden is still being generalized. Before the engine is integrated, this snapshot must be diffed against the finalized Gotaleden schema and reconciled.

The important stable concepts are expected to remain:

- source and provider provenance;
- course versions separate from race editions;
- race editions with stable `race_key` and `race_family`;
- athletes and scoped external IDs;
- relay teams and team members;
- results with both raw and normalized fields;
- checkpoints and real split observations;
- explicit relay-leg assignments.

## ÖST-specific requirements

### Multi-year identity

Every race edition must carry at least `event_key`, `year`, `race_family`, source event ID and original source race name. `config/race-catalog.json` is the authoritative pre-engine catalog.

A marketed distance label is not a course version. `course_version` remains unresolved until route geometry is verified. Years can share a comparison group without being declared identical.

### Duo

`duo60` is a relay competition on the same annual route geometry as `ultra60`. It should therefore reference the matching year's Ultra route instead of storing a duplicate route. Team membership and the two relay legs are separate data dimensions from the route itself.

### Timing observations

Only actual Sportstiming passages may become rows in `splits`. Aid stations, rescue points, cutoffs, Trace de Trail POIs and route landmarks are useful course metadata but are **not timing points unless timing evidence proves that they are**.

### Status

DNS, DNF, DSQ and other statuses must be preserved from source semantics. A runner with no finish time must not automatically be called DNF unless the source supports that interpretation.

### Identity across years

Cross-year person matching must be conservative. Names alone are insufficient for a verified identity. Sportstiming participant/result IDs, publicly exposed stable contestant IDs or other explicit source identifiers should be preferred. Ambiguous name-only matches may be used only as local/candidate identities and must never silently merge two people.

## Raw-data rule

Whenever an importer is implemented, keep the complete source row/object in `raw_json` before normalization. Do not discard unknown source fields merely because the first frontend does not use them.

## Expected staging outputs

The future ingestion pipeline should be able to produce:

1. one race record for every edition in `config/race-catalog.json`;
2. one result row per official individual/team result;
3. one split row per real checkpoint passage;
4. explicit teams/member rows for Duo;
5. source-scoped athlete identities;
6. route/course-version records only after GPX review;
7. diagnostic reports for missing/duplicate/contradictory source data.

## No-fabrication invariant

The frontend may interpolate position visually between **known** timing anchors for replay, but the data layer must never store that interpolation as a real passage, split, placing or time.
