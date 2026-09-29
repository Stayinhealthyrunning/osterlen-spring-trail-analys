# ÖST ↔ Gotaleden component contract

Datum: 2026-09-29  
Branch: `parity/gotaleden-component-by-component`

## Arbetsregel

Gotaleden `main@bd9f2aaf0466f2ad65b50d35e25981e4597350f1` är **source of truth** för ÖST:s sidordning, analysnamn, komponentplacering och interaktionsmönster.

Ultravasan `main@8d1ef31c7a820a594adf89783453154ccab4751e` används **endast** där beställningen uttryckligen kräver Ultravasans individuella analys / Runner Replay: karta direkt i profilmodalen, OpenStreetMap-bakgrund, sidopaneler med insikter/jämförelser, jämförelsemarkörer (fält/klass/kön när källstöd finns) och musiklivscykel.

ÖST får behålla egen grafisk profil: foto, färger, typografi och Österlen-signum. Data eller analyser får inte fabriceras för att uppnå visuell paritet.

## Gotaledens ordning – ska återskapas i ÖST

1. Hero
2. Loppfamilj + År / upplaga
3. Analysnavigation
4. **DELTAGARANALYS – Analysera en löpares lopp**
5. **FAVORITER – Sparade löpare**
6. **KARTA & KARTDUELL – Jämför loppet på kartan**
7. **LOPP- OCH FÄLTSTATISTIK**
8. Globala filter
9. **PERSONLIG LOPPPLAN – Måltempo**
10. KPI-rad
11. **FÖRDELNING – Måltider**
12. **BANPROFIL**
13. **STATISTIKVERKSTAD – Vad hände i loppet?**
14. **GENUSPERSPEKTIV – Fältet ur flera perspektiv**
15. **KLASS & ÅLDER – Ålderslabbet**
16. **DELSTRÄCKELABBET – Var avgjordes loppet?**
17. Historik
18. **KLUBB- OCH ORTSARENAN – Gemenskap i siffror**
19. **RESULTATDATABAS – Sök, sortera och utforska**
20. Dataprincip / metod

## Delkomponenter – exakt referens

### Toppen
- race switch
- year selector
- sticky nav: Löpare, Karta & Kartduell, Måltempo, Översikt, Statistik, Genusperspektiv, Klass & ålder, Delsträckor, Historik, Klubb & ort, Resultat
- runner search med autocomplete
- favorites
- duel search + selected chips + Direktjämförelse + Kartduell

### Översikt
- Lopp- och fältstatistik
- globala filter
- Måltempo
- KPI
- Måltider: histogram med könstoggles
- Banprofil

### Statistikverkstad
- **PLACERINGSMOTOR – Tid mot placering**
- **MÅLTIDSSIMULATOR – Vad krävs?**
- **REPET DRAS – Avhopp genom loppet**
- **FARTSIGNATUR – Delsträckornas karaktär**
- **PLACERINGSEXPRESS – Största avancemang**

### Genusperspektiv
- KPI per grupp
- **FART GENOM LOPPET – Median & spridning per delsträcka**
- **PACING – Fartretention**
- **AUTOMATISKA INSIKTER – Vad skiljer grupperna?**

### Klass & ålder
Gotaledens fasta analytiska åldersordning ska användas:
`<30`, `30–39`, `40–49`, `50–59`, `60+`.
Ordningen får **inte** sorteras efter deltagarantal.

- välj upp till fem åldersgrupper
- **ÅLDERSGRUPPER – Medianfart genom loppet**
- **UNDERLAG – Deltagande och målgång**
- **FARTKARTA – Analysgrupp × delsträcka**
- Duo använder källstödda lagklasser i stället för fabricerad individuell ålder

### Delsträckelabbet
- Course / terrain underlag där capability finns
- Från / Till / Sortera
- podium + ranking
- **FÄLTETS MÅLGÅNG – När hade fältet gått i mål?**
- **FÄLTETS FLÖDE – Så sprids startfältet**
- **PRESTATIONER SOM STICKER UT – Fem sätt att hitta ovanliga lopp**
- **SPURTVINNAREN – Årets snabbaste löpare på målspurten**, endast om en separat källstödd sista timingkontroll före mål finns. Annars visas inte komponenten.

### Historik
Samma hierarki som referensen, men prestationsmått måste fortsätta respektera ÖST:s explicit verifierade whole-course comparability. Ingen cross-year personidentitet fabriceras.

### Klubb & ort
- sök klubb
- välj upp till fyra
- selected chips
- jämförelse
- pacing
- snabbaste målgångare

### Resultat
Samma tabell- och öppna-profil-mönster som Gotaleden.

## Individuell analys / Replay – Ultravasan är source of truth

Profilmodalen ska innehålla:
- profilheader och fakta
- personlig sammanfattning / insikter
- **Replay direkt synlig utan “Visa karta”-knapp**
- riktig OpenStreetMap-bakgrund
- huvudkarta i mitten
- aktuell position / loppstatus i vänster sidopanel
- jämförelser / insikter i höger sidopanel
- uppspelning, reset, hastighet, ljud av/på, volym
- höjdprofil kopplad till samma tidslinje
- valbara jämförelsemarkörer:
  - hela fältet
  - egen klass
  - eget kön
  när respektive källstöd och minsta underlag finns
- musik startar med replay och fortsätter inom modalens livslängd; stannar/fadas ut först när profilmodalen stängs
- musikfil: `Kustlinjens steg (1).mp3`, ska lagras i ÖST assets med stabilt filnamn
- inga markörer skapas från infererade kön, klass eller saknade splits

## Förbjuden genväg

Ingen komponent ska “inspireras” fritt. För varje ändring ska implementationen kunna pekas tillbaka på motsvarande Gotaleden-komponent, eller – för den individuella Replay-delen – motsvarande Ultravasan-komponent.
