# ÖST Splits – build report

Datum: 2026-09-28  
Branch: `build/ost-splits-engine1`

## Referenser och baseline

- ÖST baseline: `e72405a13dbcd775ac20123da2bd08bc79e964f6`.
- Gotaleden implementationsreferens: `bd9f2aaf0466f2ad65b50d35e25981e4597350f1`.
- Ultravasan analys-/UX-referens: `8d1ef31c7a820a594adf89783453154ccab4751e`.
- Fryst semantiskt kontrakt: `loppanalys-engine-1.0`.

Gotaleden bidrog med den explicita modellen för individ/team, capability-driven rendering, resultattabell, profil, jämförelse och karta/replay. Ultravasan bidrog med progressiv laddning, null-säker diagrammatematik, evidensstyrd historik, CourseVersion-gränser, metodguide, responsivitet och reducerad rörelse. ÖST:s källa, adapter, branding, copy och capability-matris ligger kvar i ÖST-repot.

## Levererad produkt

Den statiska GitHub Pages-frontenden laddar `bootstrap.json`, därefter exakt en vald RaceEdition. Historiksammanställning och lokal route/elevation laddas först när användaren öppnar funktionerna. Den kompletta Engine-exporten laddas aldrig av browsern.

Frontend omfattar landningssida, global lopp-/årskontext, resultatdatabas, person-/lagprofil, favoriter, fältfilter, finishfördelning, percentiler, demografi där källan räcker, gruppanalys, split-/segmentanalys, DNF-flöde, placeringsrörelse, måltempo/loppplan, Direktjämförelse, Kartduell, flerårshistorik, metodguide samt karta/Replay där aktuell upplaga har både verkliga passager och lokal rutt.

## Portabilitetsbevis och capability-matris

| Fall | Resultat |
|---|---|
| Ultra 2018 | Resultat och verkliga splits; ingen karta/replay och ingen lånad rutt. |
| Ultra 2023 | `32 km` och `Bengtemölla` bevaras separat; primär analys använder Bengtemölla och inga depåanspråk görs. |
| Ultra 2025 | Resultat, splits, profil, lokal arrangörsrutt, höjd, Replay och Kartduell. |
| Duo 2025 | Lagsemantik, team-splits och 599-katalogens publicerade medlemsrader; `source_sequence` bevaras och `leg_no` förblir null. |
| Trail 22 2026 | Finish/resultat, demografi/klass och CourseVersion; splits/replay avstängda. |
| Trail 14 2026 | Provisorisk 13,472 km arbetsreferens beskrivs utan officiell GPX eller Replay. |
| Trail 5 2026 | Lokal rekonstruerad referens märks som rekonstruerad; inga splits eller Replay. |
| Trail 22 2018 | Resultat fungerar; course provenance förblir olöst och prestationshistorik kopplas inte. |

Samma adapter och vykomponenter hanterar alla fallen. Frontend innehåller inga regler baserade på eventnamn, ordet Ultra, ordet Duo eller platsnamn för att slå på funktioner.

## Dataintegritet

Efter bygget är de frysta invariants oförändrade: 34 genomförda RaceEditions, 9 871 resultat, 9 571 individuella deltagarrader, 300 Duo-lag, 599 medlemsrader, 6 123 observerade splitpassager och 699 derived metrics. Status är fortsatt 9 518 FINISHED, 332 DNF och 21 UNKNOWN. Källarkivet och den kuraterade databasen skyddas av versionsstyrda SHA-256-lås och testas oförändrade. Ingen Sportstiming-crawl körs i frontendbygget.

## Slutlig prestanda

| Resurs | Raw | Gzip | Budget gzip |
|---|---:|---:|---:|
| HTML | 4 362 B | 2 038 B | 32 KiB |
| CSS | 11 685 B | 3 572 B | 75 KiB |
| JavaScript, konservativt alla egna moduler | 56 813 B | 21 767 B | 256 KiB |
| Bootstrap | 31 429 B | 3 124 B | 10 KiB |
| Största valda RaceEdition | 329 247 B | 29 233 B | 600 KiB raw / 75 KiB gzip |
| Bootstrap + största RaceEdition | – | 32 357 B | 100 KiB |
| Kritisk initial väg | – | 59 734 B | 512 KiB |
| Full Engine regression guard | 5 417 505 B | 450 553 B | 750 KiB |
| Leaflet, lazy vendor | 162 363 B | 45 966 B | utanför initial väg |

Rutt/elevation är lazy. 2025–2026 Ultra-route är cirka 59,62 km med 4 246 GPX-punkter; 2024-rutten är cirka 60,60 km med 3 258 punkter. Trail 5-rutten är en separat rekonstruerad referens. Initial browserlogg visar endast bootstrap och vald RaceEdition innan användaren efterfrågar historik eller karta. Första användbara vy observerades kring 0,5 s i lokal headless Chromium; detta är en QA-observation, inte ett nätverks-SLA.

Lazy route/elevation-bundles mäter 129 053 B raw / 41 687 B gzip för Ultra 2024, 163 249 B raw / 50 567 B gzip för Ultra 2025–2026 och 6 988 B raw / 2 428 B gzip för Trail 5-referensen. Varje bundle innehåller aktuell rutt och eventuell höjdprofil och hämtas bara för vald CourseVersion.

## Test och QA

- 22 Python/unittest-fall: gröna.
- 15 Node-fall för diagrammatematik, null, capability, Duo, identitet, jämförbarhet, DNF, state, loading och loppplan: gröna.
- 11 Chromium-flöden över 1536×1024, 1366×768, 900×900 och 390×844: gröna.
- 0 console errors, 0 page errors och 0 oväntade nätverksfel.
- Foundation, prebuild och frontend performance-grind ingår i CI.

## Tillgänglighet

Leveransen har en H1, skip link, fokuserbart main, riktiga labels, `aria-current`, `aria-pressed`, `aria-sort`, tangentbordsöppningsbara resultatrader, Escape-stängning, metodrelationer och reduced-motion-läge. Diagrammens betydelse anges i text och färg används inte ensam.

## Källstyrda begränsningar

Historiska Ultra-rutter utan lokalt redistributerbart underlag får ingen karta/replay. Kortloppen saknar publicerade mellantider. Trail 14 är en arbetsreferens, Trail 5 en rekonstruktion och Trail 22 2018 har olöst årsspecifik route provenance. Historisk demografi förblir saknad där källan saknar fälten. Ingen flerårig personidentitet eller Duo member-to-leg-koppling skapas.

ÖST SPLITS READY FOR HUMAN REVIEW: YES

