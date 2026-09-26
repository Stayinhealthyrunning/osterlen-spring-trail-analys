# New race reconstruction checklist

A new race should be onboarded without changing engine code.

1. Copy `race-manifest.example.json`.
2. Give the race and course family stable IDs.
3. Enter the target year and advertised distance.
4. Add start/finish coordinates if known; otherwise add named location evidence.
5. Register every organizer map/GPX separately.
6. Register participant GPS separately from organizer evidence.
7. Add named checkpoints, bridges, aid stations, summits, roads, rivers or trail corridors.
8. Define a WGS84 network bounding box after the first georeferencing pass.
9. Run source adapters and preserve failures as explicit statuses.
10. Generate multiple candidates where branch choice is ambiguous.
11. Rank candidates and inspect hard contradictions.
12. Score evidence per segment.
13. Assign a course version only after cross-year evidence is reviewed.
14. Export candidate geometry only with its provenance sidecar.
15. Promote to validated/canonical status only when the configured promotion rules are met.

This workflow is designed so that the same reconstruction machinery can be used by future Loppanalys race projects rather than embedding race-specific assumptions in code.
