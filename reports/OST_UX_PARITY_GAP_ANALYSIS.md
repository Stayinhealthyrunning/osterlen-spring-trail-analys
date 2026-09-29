# ÖST, Ultravasan och Gotaleden – slutlig UX-paritetsanalys

Datum: 2026-09-29  
PR: #48 `improve/ost-ux-parity`  
ÖST-bas för rundan: `main@42c165f4bcead9f371348fcc0837ab96f9a2fda5`  
Referenser: `gotaleden-splits@bd9f2aaf0466f2ad65b50d35e25981e4597350f1`, `ultravasan-analys@8d1ef31c7a820a594adf89783453154ccab4751e`  
Senaste runtime-QA före denna dokumentuppdatering: `e944809c73b40e90aa7129a3315d566433e0b2e9`

## Syfte

Målet är inte att göra tre identiska webbplatser utan att ge ÖST samma produktlogik, mognad och interaktionsmönster som Gotaleden och Ultravasan, samtidigt som ÖST behåller sin egen Österlen-identitet och strikt capability-/proveniensstyrning.

## De 13 manuella granskningspunkterna

| # | Krav | Slutläge i PR #48 |
|---|---|---|
| 1 | Lägre fullbreddshero med vänstertoning | **Löst.** Fullbreddsbild, mörk vänstergradient, kompakt hero och förbättrad textkontrast. Desktop-QA låser kompakt höjd. |
| 2 | Vanlig sidladdning ska börja längst upp | **Löst.** Första laddning utan explicit deep link stannar vid `scrollY <= 2`. Explicit hash/section får fortfarande navigera till vald analys. |
| 3 | Individuell analys och Kartduell högt upp, som fokuserade popupverktyg | **Löst.** Individuell analys öppnas i profilmodal. Direktjämförelse/Kartduell öppnas i en gemensam modal från hero eller profil; Kartduellen ligger som fokuserad kartdialog. Den gamla separata Jämför-navsidan är pensionerad. |
| 4 | Personsök direkt under rubriken med autocomplete | **Löst.** Namn/lag/startnummer, sorterade förslag, Arrow Up/Down, Enter och Escape. Samma tangentbordskvalitet finns nu i jämförelseverktyget. |
| 5 | Ta bort innehållssvag “Från kust till slott”-sektion | **Löst.** Dekorativ route-journey är borttagen; Österlenberättelsen bärs av hero och familjebilder. |
| 6 | “Ditt lopp i perspektiv” ska inte vara klubb-labb | **Löst.** Kontexten heter nu **Välj lopp & upplaga**. Individverktygen ligger i hero; klubb/ort ligger längre ned i dynamiken. |
| 7 | Metod ska inte dominera; analyskort ska ha (i) | **Löst i relevant analysyta.** Full metodguide ligger i Metod. Sluttid, percentiler, klass, fältflöde, stark avslutning, status, placering, ålder, klubb, gruppsegment, delsträckor, könssegment, vald delsträcka, bana, loppplan, historik, profil/replay och direktjämförelse har lokal metodhjälp. |
| 8 | Mer interaktivitet i diagram | **Löst där interaktion är meningsfull.** Kvinna/man kan tändas/släckas i sluttid, percentiler, könskort, placering och segment. Klass/klubb-staplar kan filtrera hela analysen. Placeringens punkter öppnar profil. |
| 9 | Percentiler ska använda rutan bättre och visa kvinnor/män med staplar | **Löst.** Gemensam P10–P90-tröskel, kumulativa kvinna/man-staplar, antal/n och respektive köns egen percentiltid. |
| 10 | “Bröt” ska vara DNF | **Löst.** Publika analysytor använder DNF. DNS och övriga statusar har tydliga svenska etiketter där det är lämpligt. |
| 11 | Klass/ålder ska inte vara jättetabeller | **Löst.** Klasser och klubb/ort har stapelöversikt med detaljer på begäran. Ålder har femårsdiagram, median/Q25–Q75 och kompakt åldersklassöversikt med expanderbar detalj. |
| 12 | Fältflöde utan trivial Start=100%; färre onödiga fullbreddskort | **Löst.** Startpunkten utelämnas. Fältflöde, könsstatus, ålder och klubb/ort använder tätare tvåkolumnslayout; fullbredd reserveras för analyser som behöver den. |
| 13 | Samma familj som Gotaleden/Ultravasan | **Löst på produktmönsternivå.** Topplacerade individverktyg, modal profil/jämförelse/kartduell, autocomplete, favoriter, interaktiva serier, gruppanalys, segment, bana, historik, lokal metodhjälp, keyboard/reduced-motion och gemensam informationshierarki är nu samstämda. ÖST behåller egen färg, bildvärld och typografi. |

## Funktionell referensparitet

| Referensmönster | ÖST |
|---|---|
| Tidig löpar-/resultatsökning | Hero-sök med direkt profilmodal |
| Individuell Runner Analysis | Profil, KPI, Journey, passager, relativ delsträcka, Replay där capability finns, favoriter och direkt väg till jämförelse |
| Head-to-head / Direktjämförelse | Gemensam jämförelsemodal med två resultat, passage-/segmentgap och observerade duellinsikter |
| Kartduell | 2–5 resultat där lokal rutt + verkliga passager medger Replay; annars exakt två för direktjämförelse |
| Kvinna/man-serier | Interaktiva toggles i relevanta diagram och segment; saknat kön infereras aldrig |
| Percentiler / finish progression | Gemensamma trösklar, könsstaplar, n och källtäckning |
| Fält-/DNF-flöde | Verkliga passager och sista observerade DNF-kontroll |
| Klass-/klubbgrupper | Visuell översikt, snabbfilter, expanderbar detalj och delsträcksjämförelse |
| Course Intelligence-principer | Banversion/proveniens, höjd/rutt när tillåtet, D+/D− bara vid komplett höjdprofil, måltempo/loppplan |
| Historik | Explicit whole-course-jämförbarhet, inställda år som luckor, könstäckning, fingeravtryck och toppnotering |
| Metod / accessibility | (i)-hjälp, samlad metod, `aria-current`, keyboard, fokusåterställning, reduced motion och tile-fallback |

## Medvetna skillnader – inte kvarvarande UX-gap

- Ingen cross-year personhistorik/Hall of Fame utan verifierad identitetskoppling.
- Ingen Duo member→leg-inferens.
- Ingen Replay för splitlösa Trail 22/14/5.
- Ingen lånad historisk rutt.
- Ingen syntetisk sammanvägd difficulty score.
- Ingen prestationslinje över år utan uttrycklig whole-course-jämförbarhet.
- ÖST:s fotografiska kust-/våridentitet är medvetet rikare än referensernas branding.

Dessa skillnader är evidens- och produktbeslut. De ska inte fyllas med heuristik för att uppnå kosmetisk paritet.
