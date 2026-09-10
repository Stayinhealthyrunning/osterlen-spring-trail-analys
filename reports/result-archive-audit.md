# Audit av fryst ÖST-resultatarkiv

Status: **PASS**

- Resultat: **9,871**
- Mellantider: **5,382**
- Härledda checkpointmått: **610**
- År/distans-importer: **34**
- Källfel: **0**
- SQLite integrity_check: **ok**
- SQLite SHA-256 matchar frysningsrapport: **True**
- Gzip SHA-256 matchar frysningsrapport: **True**

## Kritiska kontroller

| Kontroll | Värde |
|---|---:|
| `import_count_mismatches` | 0 |
| `empty_imports` | 0 |
| `duplicate_source_result_keys` | 0 |
| `blank_result_uids` | 0 |
| `blank_source_result_ids` | 0 |
| `finished_without_time` | 0 |
| `nonfinished_with_time` | 0 |
| `nonpositive_finish_times` | 0 |
| `splits_without_parent` | 0 |
| `negative_split_seconds` | 0 |
| `derived_negative_seconds` | 0 |
| `split_chronology_errors` | 0 |
| `final_split_finish_mismatches_gt_2s` | 0 |

## Statusfördelning

| Status | Antal |
|---|---:|
| FINISHED | 9518 |
| UNKNOWN | 353 |

## UNKNOWN per år/familj

| År | Familj | Typ | Antal |
|---:|---|---|---:|
| 2018 | trail14 | athlete | 2 |
| 2018 | trail22 | athlete | 18 |
| 2018 | ultra60 | athlete | 25 |
| 2019 | duo60 | team | 2 |
| 2019 | trail14 | athlete | 3 |
| 2019 | trail22 | athlete | 3 |
| 2019 | ultra60 | athlete | 35 |
| 2022 | trail14 | athlete | 3 |
| 2022 | trail22 | athlete | 3 |
| 2022 | ultra60 | athlete | 36 |
| 2023 | duo60 | team | 2 |
| 2023 | trail22 | athlete | 1 |
| 2023 | ultra60 | athlete | 24 |
| 2024 | duo60 | team | 2 |
| 2024 | trail14 | athlete | 1 |
| 2024 | trail22 | athlete | 5 |
| 2024 | ultra60 | athlete | 90 |
| 2025 | duo60 | team | 5 |
| 2025 | trail14 | athlete | 3 |
| 2025 | trail22 | athlete | 2 |
| 2025 | ultra60 | athlete | 29 |
| 2026 | duo60 | team | 5 |
| 2026 | trail14 | athlete | 3 |
| 2026 | trail22 | athlete | 9 |
| 2026 | ultra60 | athlete | 42 |

## Checkpointtäckning

| År | Familj | Källpunkt | Semantik | Passager | Saknar elapsed |
|---:|---|---|---|---:|---:|
| 2018 | ultra60 | Stenshuvud km 14 | stenshuvud | 150 | 0 |
| 2018 | ultra60 | Bengtemölla km 32 | bengtemolla | 140 | 0 |
| 2018 | ultra60 | Finish | finish | 125 | 0 |
| 2018 | ultra60 | Vantalängan km 52 | vantalangan | 125 | 0 |
| 2019 | ultra60 | Bengtemölla km 32 | bengtemolla | 126 | 0 |
| 2019 | ultra60 | Stenshuvud km 14 | stenshuvud | 213 | 0 |
| 2019 | ultra60 | Vantalängan km 52 | vantalangan | 242 | 0 |
| 2019 | ultra60 | Finish Km 60+ | finish | 243 | 0 |
| 2022 | ultra60 | 32 km | bengtemolla_approach | 308 | 0 |
| 2022 | ultra60 | 62 km | finish | 282 | 0 |
| 2022 | ultra60 | Bengtemölla | bengtemolla | 294 | 0 |
| 2023 | ultra60 | 32 km | bengtemolla_approach | 320 | 0 |
| 2023 | ultra60 | 62 km | finish | 306 | 0 |
| 2023 | ultra60 | Bengtemölla | bengtemolla | 316 | 0 |
| 2024 | ultra60 | 34 km | bengtemolla | 362 | 0 |
| 2024 | ultra60 | 60 km | finish | 330 | 0 |
| 2025 | ultra60 | 34 km | bengtemolla | 386 | 0 |
| 2025 | ultra60 | 60 km | finish | 371 | 0 |
| 2026 | ultra60 | 34 km | bengtemolla | 376 | 0 |
| 2026 | ultra60 | 60 km | finish | 367 | 0 |

## Statusord funna i UNKNOWN-rådata

- `utgått`: 318

## Tolkning

- `PASS` betyder att arkivet är tekniskt helt, internt konsistent och täcker alla 34 förväntade år×distans-importer.
- `UNKNOWN` är medvetet inte likställt med DNF/DNS. Det kräver uttrycklig källa eller separat validerad statuslogik.
- Demografi/klubb/nationalitet kan saknas i Sportstiming och behandlas som datatäckning, inte importfel.
