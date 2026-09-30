# ÖST route coverage — publication state after route materialization

Updated 2026-09-30.

A local route asset can be one of three things:

1. **Arrangörs-GPX** — organizer-hosted GPX bytes archived locally.
2. **Publik banreferens · Trace de Trail** — derived local route from geometry embedded in the public Trace de Trail map page. This is not an authenticated GPX export and is not labelled organizer GPX.
3. **Rekonstruerad bana** — a clearly labelled reconstruction supported by organizer material and independent controls.

Trace de Trail's GPX export currently requires login. No access control is bypassed.

| Family | Editions | Local route | Provenance | Frontend |
|---|---|:---:|---|---|
| Ultra 60 | 2018 | Yes | Public Trace geometry 43970, date 2018 verified | Map + elevation; Replay withheld |
| Ultra 60 | 2019 | Yes | Public Trace geometry 69381, date 2019 verified | Map + elevation; Replay withheld |
| Ultra 60 | 2022–2023 | Yes | Public Trace geometry 172147 / exact peer 203147 | Map + elevation + Replay |
| Ultra 60 | 2024 | Yes | Archived organizer GPX | Map + elevation + Replay |
| Ultra 60 | 2025–2026 | Yes | Archived organizer GPX | Map + elevation + Replay |
| Duo 60 | 2019 | Yes | Inherits Ultra 2019 route | Map + elevation; Replay withheld |
| Duo 60 | 2022–2023 | Yes | Inherits Ultra 2022–23 route | Map + elevation + Replay |
| Duo 60 | 2024–2026 | Yes | Inherits same-year organizer Ultra route | Map + elevation + Replay |
| Trail 22 / 21 | 2018 | **No** | Candidate Trace 7897 is dated 2016 | Explicit no-route explanation |
| Trail 22 / 21 | 2019 | Yes | Public Trace geometry 69864, date verified | Map + elevation; no split Replay |
| Trail 22 / 21 | 2022–2024 | Yes | Public Trace geometry 165617, exact peers 203146/237224 | Map + elevation; no split Replay |
| Trail 22 / 21 | 2025–2026 | Yes | Public Trace geometry 322314, exact peer 280053 | Map + elevation; no split Replay |
| Trail 14 / 13 | 2018–2025 | **No** | No verified year-specific geometry | Explicit no-route explanation |
| Trail 14 / 13 | 2026 | Yes | 13.472 km provisional Hallamölla splice reference | Map + elevation, labelled provisional; no split Replay |
| Trail 5 | 2018–2025 | **No** | Historical geometry unresolved | Explicit no-route explanation |
| Trail 5 | 2026 | Yes | Organizer-raster/OSM reconstruction | Map, labelled reconstructed; elevation remains source-dependent |

## Publication rules

- Route geometry is never borrowed from another course version merely because the marketing distance is similar.
- Exact Trace geometry matches can support one shared course version when already established in `config/course-versions.json`.
- 2018 Trail 21/22 remains deliberately unassigned because the available Trace candidate has a 2016 competition date.
- Trail 13/14 2026 remains a **working reconstructed reference**, not authoritative GPX.
- Map availability and Replay availability are separate. A map does not enable Replay unless timing checkpoints and route-anchor mapping are also verified.
