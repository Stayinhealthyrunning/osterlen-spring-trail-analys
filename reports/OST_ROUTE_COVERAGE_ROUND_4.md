# ÖST route coverage — review round 4

This matrix records the local route assets that the frontend may publish. Verified public geometry without a redistributable local asset does not qualify as a frontend route.

| Race family | Editions | Local route | Type and provenance | Frontend result |
| --- | --- | --- | --- | --- |
| Ultra 60 | 2018, 2019, 2022, 2023 | No | Verified public geometry/course versions, but no approved local route asset | Explicit no-route explanation; no route is borrowed |
| Ultra 60 | 2024 | Yes | Archived organizer GPX, `ultra60-2024` | Map and elevation profile |
| Ultra 60 | 2025, 2026 | Yes | Archived organizer GPX, shared organizer source `ultra60-2025-2026` | Map and elevation profile |
| Duo 60 | 2019, 2022, 2023 | No | Correct Ultra course version is assigned, but that version has no approved local asset | Explicit no-route explanation; no route is borrowed |
| Duo 60 | 2024 | Yes | Same explicitly assigned organizer route as Ultra 60 2024 | Map and elevation profile |
| Duo 60 | 2025, 2026 | Yes | Same explicitly assigned organizer route as Ultra 60 2025–2026 | Map and elevation profile |
| Trail 22 / 21 | 2018 | No | No year-specific approved course version | Explicit no-route explanation |
| Trail 22 / 21 | 2019, 2022–2026 | No | Verified public geometry and comparison groups; redistribution/local route asset is unavailable | Explicit no-route explanation; external geometry is not republished |
| Trail 14 / 13 | 2018–2025 | No | No year-specific approved local route | Explicit no-route explanation |
| Trail 14 / 13 | 2026 | No | Provisional 13.472 km Hallamölla splice working reference; no stored route geometry | Explicit no-route explanation; provisional recipe is not rendered as GPS |
| Trail 5 | 2018–2025 | No | Historical short-course geometry remains unassigned | Explicit no-route explanation |
| Trail 5 | 2026 | Yes | Validated reconstruction from organizer raster snapped to OSM; not an organizer GPX; no usable elevation values | Map labelled `Rekonstruerad bana`; no fabricated elevation profile |

The round-4 frontend fix concerns Trail 5: the allowed route was present in the payload, but the overview map mount previously required an elevation SVG. Because the reconstructed route has no elevation samples, that guard hid its map. Map mounting is now independent of elevation availability.
