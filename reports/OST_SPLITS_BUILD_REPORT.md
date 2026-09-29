# ÖST Splits – build report

Datum: 2026-09-29  
PR: #48 `improve/ost-ux-parity`  
Runtime-QA: `e944809c73b40e90aa7129a3315d566433e0b2e9`

## Referenser

- ÖST Engine-/systembas: `main@42c165f4bcead9f371348fcc0837ab96f9a2fda5`
- Gotaleden Engine-/UX-referens: `bd9f2aaf0466f2ad65b50d35e25981e4597350f1`
- Ultravasan UX-/analysreferens: `8d1ef31c7a820a594adf89783453154ccab4751e`
- Semantiskt kontrakt: `loppanalys-engine-1.0`

PR #48 är en produkt-/UX-runda ovanpå den auditerade Engine 1.0-implementationen. Frysta source data och provenance-kontrakt ändras inte.

## Levererad produkt

ÖST använder nu samma centrala produktmönster som referensverktygen:

- kompakt fullbreddshero med primär löparsök,
- topplacerad individuell analys,
- topplacerad Direktjämförelse/Kartduell i modal,
- autocomplete och keyboard-flöde,
- capability-driven långscroll,
- sticky ankarnavigation,
- resultatdatabas,
- profil/favoriter,
- interaktiva kvinna/man-serier,
- sluttid och percentiler,
- klass/ålder/klubb som visualisering först och tabell på begäran,
- DNF-/fältflöde,
- segment/spridning/placeringsrörelse,
- relativ deltagarprestation mot fältmedian,
- bana/proveniens/höjd,
- måltempo/loppplan,
- historisk jämförbarhet och fingeravtryck,
- lokal (i)-metodik + full Metod-sektion,
- Replay/Kartduell endast där capability medger det.

ÖST:s visuella uttryck är fortfarande eget: Österlenkust, vår, blomning, skog och fem familjespecifika miljöbilder.

## Data och capability

Oförändrade totals:

- 34 genomförda RaceEditions
- 9 871 resultat
- 6 123 observerade splits/mellantider
- 300 Duo-lag
- 599 lagmedlemsrader

Samma adapter/vylogik hanterar:

- modern Ultra med splits + lokal rutt + Replay,
- äldre Ultra med splits men utan lånad rutt,
- Duo som team utan fabricerad member→leg,
- Trail 22/14/5 med finish-only-analys där splits saknas,
- provisorisk/rekonstruerad geometri med tydlig provenance.

## Slutlig performance

| Resurs | Raw | Gzip | Budget |
|---|---:|---:|---:|
| HTML | 4 086 B | 1 693 B | 32 KiB gzip |
| CSS | 48 566 B | 11 240 B | 75 KiB gzip |
| JavaScript | 110 075 B | 35 650 B | 256 KiB gzip |
| Bootstrap | – | 3 143 B | 10 KiB gzip |
| Största valda RaceEdition | 329 247 B | 29 234 B | 600 KiB raw / 75 KiB gzip |
| Bootstrap + största RaceEdition | – | 32 377 B | 100 KiB gzip |
| Full Engine | 5 417 501 B | 450 542 B | 750 KiB gzip |
| Kritisk initial kod/data | – | 80 960 B | 512 KiB gzip |

Route, elevation, replay och Leaflet är fortsatt lazy. Historiken levereras som purpose-built aggregate och alla 9 871 resultat hydreras aldrig vid initial start.

## Test och QA

På runtime-QA-commit `e944809c73b40e90aa7129a3315d566433e0b2e9`:

- Foundation: grön
- Prebuild: grön
- 25 Python-tester: gröna
- 27 JavaScript-tester: gröna
- 20 Chromium-flöden: gröna
- alla 34 upplagor capability-testade
- 1536×1024, 1366×768, 900×900, 390×844 utan document overflow
- 0 console/page/unexpected-network errors
- lokal first useful view cirka 452 ms

## Viktiga regressionsgrindar

- sida utan explicit deep link öppnar högst upp,
- hero är fullbredd och kompakt,
- individuell sök/autocomplete öppnar profilmodal,
- profil kan gå direkt till jämförelsemodal,
- jämförelsesök har keyboard autocomplete,
- Direktjämförelse och Kartduell är fokuserade dialogflöden,
- DNF används som publik term,
- kvinnor/män kan tändas/släckas där parallella diagramserier finns,
- Fältflöde utelämnar trivial Start=100 %,
- ålder/klass/klubb har visuella översikter,
- gamla Ultra/Duo-checkpoints är kronologiska,
- finish-only-familjer får inga syntetiska splits/replay,
- reduced motion och tile-failure fallback fungerar.

## Medvetna evidensgränser

Ingen cross-year personidentitet, Duo member→leg, syntetisk split, lånad historisk bana eller syntetisk difficulty score skapas. Historisk prestation kräver explicit whole-course-jämförbarhet.

**ÖST SPLITS READY FOR HUMAN REVIEW: YES**
