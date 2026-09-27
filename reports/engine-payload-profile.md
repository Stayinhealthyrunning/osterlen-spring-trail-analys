# ÖST Engine 1.0 payload profile

Generated from the real frozen/curated Engine 1.0 export. Payload SHA-256: 13f4a1470e3c305047c226187364376faf553ded9e3efa73e4f5ce423b0d62e8.

## Whole payload

- Raw/minified JSON: **5.2 MiB** (5,417,501 bytes)
- gzip -9: **440.0 KiB** (450,548 bytes)
- gzip/raw ratio: **0.083**

## Bootstrap candidate

Contains event, race catalog, course metadata and source/version metadata, but no result rows/splits.

- Raw: **26.4 KiB**
- gzip: **1.9 KiB**

## Top-level contribution

| Section | Raw | gzip |
|---|---:|---:|
| races | 3.7 MiB | 338.8 KiB |
| splits | 1.2 MiB | 83.1 KiB |
| team_members | 170.4 KiB | 9.5 KiB |
| teams | 35.9 KiB | 4.8 KiB |
| race_catalog | 22.9 KiB | 1.2 KiB |
| checkpoints | 17.8 KiB | 648 B |
| courses | 3.1 KiB | 625 B |
| sources | 163 B | 140 B |
| event | 125 B | 117 B |
| engine_contract | 23 B | 43 B |

## Largest selected race bundles

A selected-race bundle is race metadata + all result records + checkpoints + real splits + team/member rows for one edition.

| Race | records | splits | raw | gzip |
|---|---:|---:|---:|---:|
| ost-2025-ultra60 | 400 | 757 | 304.6 KiB | 28.5 KiB |
| ost-2024-ultra60 | 420 | 692 | 299.2 KiB | 28.0 KiB |
| ost-2026-ultra60 | 409 | 743 | 304.5 KiB | 27.9 KiB |
| ost-2023-ultra60 | 330 | 942 | 321.4 KiB | 25.2 KiB |
| ost-2022-ultra60 | 318 | 884 | 304.1 KiB | 24.6 KiB |
| ost-2025-trail22 | 520 | 0 | 196.7 KiB | 20.7 KiB |
| ost-2024-trail22 | 506 | 0 | 191.0 KiB | 20.4 KiB |
| ost-2019-ultra60 | 278 | 824 | 292.8 KiB | 20.1 KiB |
| ost-2026-trail22 | 504 | 0 | 190.6 KiB | 19.6 KiB |
| ost-2026-trail14 | 456 | 0 | 171.3 KiB | 17.2 KiB |

## Delivery implication

- Monolithic initial payload: **440.0 KiB gzip** before route/elevation assets.
- Bootstrap + largest selected race: **30.4 KiB gzip**.
- Bootstrap + median selected race: **15.1 KiB gzip**.
- Route and elevation assets are separate and should remain lazy-loaded.

This report measures transport size only. Browser parse/render cost and map/replay memory must be measured once the frontend exists.
