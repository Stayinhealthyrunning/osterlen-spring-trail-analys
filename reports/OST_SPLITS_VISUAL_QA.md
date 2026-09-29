# ÖST Splits – visuell och funktionell QA

Datum: 2026-09-29  
Branch: `improve/ost-ux-parity`  
Runtime-QA: `d9a3c32b90b27ab4519b913323f7c977ea404b5c`

## Slutresultat

Den fulla PR #48-polishen är browserverifierad och manuellt screenshotgranskad. Hero, individverktyg, analysflöde, interaktiva serier, kompakta gruppvyer, profil, jämförelsemodal, Kartduell, historia och metodik håller ihop som samma verktygsfamilj som Gotaleden/Ultravasan, men med ÖST:s egen grafiska profil.

### Automatiserad regression

- Foundation validation: **success**
- Prebuild readiness: **success**
- Python: **25/25**
- JavaScript: **27/27**
- Chromium: **20/20 flöden**
- Alla **34 RaceEditions** renderade med capability-gating
- 1536×1024, 1366×768, 900×900 och 390×844 utan document overflow
- 0 console errors
- 0 page errors
- 0 oväntade nätverksfel
- första användbara vy i lokal headless Chromium: cirka **326 ms** (QA-observation, inte SLA)

## Visuell granskning

| Yta | Resultat |
|---|---|
| Hero | Fullbreddsbild med vänstergradient, tydlig vit text, kompakt höjd och sök/verktyg inom samma visuella zon. |
| Familjekort | Fem egna miljöbilder och balanserad kortstorlek; Trail 22/14/5 använder inland/skog snarare än falsk kustidentitet. |
| Lopp/upplaga | Neutral **Välj lopp & upplaga**-kontext; klubb/ort ligger inte längre i toppens individperspektiv. |
| Översikt | KPI-rad, histogram och percentilstaplar i balanserat tvåkolumnspar; könsöversikt och klassvisualisering följer logiskt. |
| Dynamik | Status + Fältflöde delar rad. Interaktiv placering följs av könsstatus + separat DNF-lokalisering, Stark avslutning och ålder/klubb. Den duplicerade Percentiltrappan är borttagen. |
| Ålder | Exakt ålder visualiseras i femårsintervall; åldersklasser har stapelöversikt och valfri detalj. |
| Klass/klubb | Skannbara horisontella staplar; klass/klubb kan filtrera analysen direkt; full tabell finns på begäran. |
| Segment | Huvuddiagram och tabell följt av interaktiv kvinna/man-jämförelse och vald delsträcka. |
| Bana | Proveniens först, karta/höjd lazy, måltempo/loppplan separat med lokal metodhjälp. |
| Historik | Fingeravtryck, toppnotering och kön över tid ligger före den fullständiga årstabellen; jämförbarhet syns. |
| Metod | Full guide ligger sist i analysflödet; metodiken är inte längre en stor barriär nära toppen. |
| Profil | Fokuserad dialog med KPI, favoriter, Journey, relativ delsträcka, metodhjälp och Replay där capability finns. |
| Jämförelse | Fokuserad modal med sökning, valda deltagare, två balanserade resultatkort, tidsskillnad, passager/delsträckor och Kartduell. |
| Mobil | Hero, profil och jämförelsemodal ligger inom viewport; bred data scrollar lokalt i komponent i stället för att spräcka dokumentet. |

## Interaktioner som är verifierade

- vanlig sidladdning utan deep link stannar längst upp,
- hero-sök: namn/lag/startnummer, tangentbordsautocomplete och direkt profil,
- jämförelsesök: autocomplete med Arrow Up/Down, Enter/Escape,
- profil → **Jämför detta resultat** → samma jämförelsemodal,
- kvinna/man-toggle i sluttid, percentiler, könsöversikt, placement scatter och segment,
- klass- och klubb/ort-staplar som snabbfilter,
- placement scatter → profil via mus eller tangentbord,
- ankarnavigation + deep links + browser Back/Forward,
- Resultatdatabas, sortering, pagination och keyboard-profile,
- måltempo/loppplan,
- route/elevation + Runner Replay,
- Kartduell inklusive avsiktligt tile-failure-test,
- reduced-motion,
- Duo-teamflöde,
- äldre Ultra med splits men utan lånad rutt,
- finish-only-familjer utan fabricerade segment/replay.

## Terminologi och data

Publik status använder **DNF** i stället för “Bröt”. Kvinna/man visas bara från källstödda uppgifter. Start=100 % visas inte i Fältflöde. Metodinfo finns lokalt på relevanta analyskort och den fullständiga metoden ligger i Metod.

Datatotalerna är oförändrade: 34 lopp, 9 871 resultat, 6 123 observerade mellantidspassager, 300 Duo-lag och 599 lagmedlemsrader. Source data, Engine 1.0, provenance och capability-regler är oförändrade.

## Prestanda

Senaste fulla runtime-QA:

- HTML: **1 693 B gzip**
- CSS: **11 563 B gzip**
- JavaScript: **35 709 B gzip**
- bootstrap: **2 049 B gzip**
- största valda racebundle: **29 234 B gzip**
- bootstrap + största racebundle: **31 283 B gzip**
- full Engine: **450 542 B gzip**
- kritisk initial kod/data: **81 342 B gzip** av 524 288 B budget
- route/elevation/replay och Leaflet förblir lazy-loadade

Bilder ingår inte i performance-kontraktets kritiska kod/data-budget.

**VISUAL QA READY FOR HUMAN REVIEW: YES**


### Sista manuella kontrollpunkter

Den sista screenshotgranskningen fokuserade särskilt på kortbalans och flödesrytm. Histogram/percentiler behåller gemensam höjd, medan sekundära kort återgår till naturlig höjd. Könsöversikt och klassfördelning delar rad utan att bli två separata fullbreddsblock. DNF-lokalisering ligger som eget kort bredvid könsstatus. Historiken har endast en sektionsrubrik. Jämförelsemodalen visar tydligt hur många resultat som är valda och kan nollställas utan att stängas.
