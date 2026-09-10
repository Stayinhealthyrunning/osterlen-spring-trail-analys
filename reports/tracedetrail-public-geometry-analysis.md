# Trace de Trail public geometry analysis

Den publika kartgeometrin analyseras **endast transient**. Koordinatserien sparas inte i repot och den inloggningsskyddade GPX-exporten används inte.

## Banor

| Familj | År | Trace | datum i Trace | punkter | kartgeometri km | Trace km | geometry hash |
|---|---:|---:|---|---:|---:|---:|---|
| `trail22` | 2018 | 7897 | 16/04/2016 ⚠ | 1516 | 21.688 | 21.7 | `98400a8a0f05` |
| `trail22` | 2019 | 69864 | 13/04/2019 | 1345 | 21.726 | 21.8 | `ee8ab4532a44` |
| `trail22` | 2022 | 165617 | 09/04/2022 | 1395 | 21.741 | 21.8 | `4e6dd245a2aa` |
| `trail22` | 2023 | 203146 | 15/04/2023 | 1395 | 21.741 | 21.8 | `4e6dd245a2aa` |
| `trail22` | 2024 | 237224 | 13/04/2024 | 1395 | 21.741 | 21.8 | `4e6dd245a2aa` |
| `trail22` | 2025 | 280053 | 12/04/2025 | 1395 | 21.710 | 21.77 | `f10e7f489055` |
| `trail22` | 2026 | 322314 | 18/04/2026 | 1395 | 21.710 | 21.77 | `f10e7f489055` |
| `ultra60` | 2018 | 43970 | 14/04/2018 | 2872 | 62.055 | 62.6 | `bb0a90f2178e` |
| `ultra60` | 2019 | 69381 | 13/04/2019 | 4033 | 58.612 | 58.7 | `ba16b78ba883` |
| `ultra60` | 2022 | 172147 | 09/04/2022 | 3552 | 58.347 | 58.5 | `d65a4c4f6156` |
| `ultra60` | 2023 | 203147 | 15/04/2023 | 3552 | 58.347 | 58.5 | `d65a4c4f6156` |
| `ultra60` | 2024 | 251126 | 13/04/2024 | 3258 | 60.598 | 60.7 | `2c8774fa3e20` |
| `ultra60` | 2025 | 272846 | 13/04/2025 | 4246 | 59.592 | 59.76 | `57e39f38d4f8` |
| `ultra60` | 2026 | 322315 | 18/04/2026 | 4269 | 59.592 | 59.76 | `29af78c7e734` |

## Jämförelse mot närliggande tävlingsår

| Familj | År A | År B | exakt hash | inom 50 m | inom 100 m | Δ km | klassning |
|---|---:|---:|:---:|---:|---:|---:|---|
| `trail22` | 2018 | 2019 | — | 100.0% | 100.0% | +0.038 | same_course_geometry_strong |
| `trail22` | 2019 | 2022 | — | 99.3% | 100.0% | +0.015 | same_course_geometry_strong |
| `trail22` | 2022 | 2023 | ✓ | 100.0% | 100.0% | +0.000 | exact_same_public_geometry |
| `trail22` | 2023 | 2024 | ✓ | 100.0% | 100.0% | +0.000 | exact_same_public_geometry |
| `trail22` | 2024 | 2025 | — | 99.3% | 100.0% | -0.031 | same_course_geometry_strong |
| `trail22` | 2025 | 2026 | ✓ | 100.0% | 100.0% | +0.000 | exact_same_public_geometry |
| `ultra60` | 2018 | 2019 | — | 94.7% | 97.4% | -3.443 | largely_same_corridor_with_changes |
| `ultra60` | 2019 | 2022 | — | 99.2% | 100.0% | -0.265 | same_course_geometry_strong |
| `ultra60` | 2022 | 2023 | ✓ | 100.0% | 100.0% | +0.000 | exact_same_public_geometry |
| `ultra60` | 2023 | 2024 | — | 92.6% | 93.4% | +2.251 | substantial_shared_corridor_but_material_changes |
| `ultra60` | 2024 | 2025 | — | 94.1% | 97.9% | -1.006 | largely_same_corridor_with_changes |
| `ultra60` | 2025 | 2026 | — | 100.0% | 100.0% | +0.000 | same_course_geometry_strong |

## Namngivna checkpoints/serviceställen projekterade på kartgeometrin

| Familj | År | Landmark | km | restavstånd |
|---|---:|---|---:|---:|
| `ultra60` | 2018 | bengtemolla | 33.479 | 0.0 m |
| `ultra60` | 2018 | vantalangan | 53.611 | 0.0 m |
| `ultra60` | 2022 | bengtemolla | 32.212 | 0.0 m |
| `ultra60` | 2023 | bengtemolla | 32.212 | 0.0 m |
| `ultra60` | 2025 | bengtemolla | 33.479 | 0.0 m |
| `ultra60` | 2025 | vantalangan | 51.221 | 0.0 m |
| `ultra60` | 2026 | bengtemolla | 33.479 | 0.0 m |
| `ultra60` | 2026 | vantalangan | 51.221 | 0.0 m |

## Proveniensvarningar

- `trail22` 2018, trace 7897: `dateCompet=16/04/2016`.
