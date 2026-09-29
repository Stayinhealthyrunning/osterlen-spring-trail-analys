# ÖST Splits – visuell designbrief

Datum: 2026-09-28  
Status: source of truth för produktens visuella uttryck

## Primär visuell referens

`research/ost-grafisk-profil.png` ska inspekteras visuellt vid större designändringar. Bilden är primär referens för atmosfär, komposition, kust- och vårkänsla, redaktionell rikedom och resan från hav till slott. Den är ett koncept, inte en datakälla: inbakade exempelresultat, porträtt, kartlinjer och byggnadsbilder får inte kopieras som sakuppgifter.

Produktens heroasset `docs/assets/ost-coast-hero.webp` är en separat, textfri och icke platsidentifierande landskapsbild framtagen med referensen som stämnings- och kompositionsunderlag. Familjekorten använder egna optimerade WebP-miljöer: kust och löpare för Ultra 60, kust/inland och två löpare för Duo 60, bäck och bokskog för Trail 22 samt två skilda intima inlandsskogar för Trail 14 och Trail 5. Bilderna uttrycker miljökaraktär utan att påstå att en viss kvarn, byggnad eller exakt namngiven plats avbildas. Namngivna platser presenteras endast som text eller med verifierade visuella källor. Den redaktionella miljöresan skiljs uttryckligen från tidtagningspunkter och banversioner.

## Identitet

ÖST Splits ska kännas som en varm, professionell analysprodukt för resan från Österlensk kust till Christinehof. Landningsytan får bära vår, hav, sand och löpning. Analysytorna ska vara lugnare och prioritera läsbar data. Namngivna verkliga platser illustreras bara när formen bygger på verifierade referenser; hero-fotot skapar kustkänsla utan att göra anspråk på att avbilda en viss byggnad eller exakt plats.

## Design tokens

| Roll | Token | Värde |
|---|---|---|
| Östersjöblå | `--sea` | `#1677A8` |
| Mörk havsblå | `--sea-dark` | `#09577E` |
| Sand | `--sand` | `#E8D8BE` |
| Vårgrön | `--spring` | `#8FBE63` |
| Blomningsrosa | `--pink` | `#E7A6B7` |
| Blomningsvit | `--warm` | `#FFF8F0` |
| Christinehof-gul | `--gold` | `#D9A441` |
| Mörk text | `--ink` | `#243746` |

Diagram använder blått och grönt som primära analysfärger. Källstödda kvinnor visas rosa (`#B51D60`) och män blått (`#2563EB`), alltid tillsammans med text. DNF, saknad data och rekonstruerad geometri har även etiketter eller mönster; färg bär aldrig betydelsen ensam.

## Typografi och layout

UI, tabeller och diagram använder en Manrope-liknande systemstack. Hero och redaktionella rubriker använder en Fraunces-liknande serifstack. Inga webbfonter laddas vid runtime. Analyskort har varmvit bakgrund, diskret kant, 15 px hörnradie och mycket återhållsam skugga.

Desktop använder högst två analyskolumner. Metodguiden använder fyra, två respektive en kolumn vid desktop, tablet och mobil. Komplexa tabeller och SVG-diagram får egen horisontell scroll; dokumentet får inte överskrida viewporten med mer än 2 px. Mobilens familjekort och analysnavigation är horisontellt bläddringsbara för att bevara läsbar storlek.

Den centrala analysen är ett sammanhängande scrollbart dokument. Sticky navigation länkar till Översikt, Loppets dynamik, Delsträckor, Bana / Course Intelligence, Historisk översikt och Metod när respektive underlag finns. Resultatdatabas och individuell jämförelse är separata arbetsvyer. Hashankare ska kunna återställa och fokusera en analyssektion via deep link och browserhistorik.

## Komponentprinciper

- Första viewporten prioriterar startande, fullföljare, mediantid och DNF.
- Resultatrader kan fokuseras och öppnas med Enter eller mellanslag.
- Replay placeras högt i person- och lagprofil när capability tillåter det.
- Tomma lägen förklarar den konkreta källbegränsningen och lämnar inte tomma diagramytor.
- Metodknappar använder unika relationer via `aria-controls`, `aria-describedby` och `aria-expanded`.
- `prefers-reduced-motion` stoppar automatisk replay men behåller tidsreglaget.

## Proveniensspråk

Diskreta badges och metodtexter använder: **Källvärde**, **Beräknat**, **Jämförbart**, **Aktuellt urval**, **Arrangörs-GPX**, **Rekonstruerad bana**, **Arbetsreferens** och **Begränsat underlag**. Verifierad CourseVersion, lokal ruttfil och helbanans jämförbarhet presenteras som separata egenskaper.

## Kartor och felhantering

Kartan startar som en neutral vektorvy med den lokala rutten. Kartbakgrund hämtas först efter användarens val. Om tiles fallerar tas de bort och rutten, kontrollerna och deltagarna ligger kvar. Det gör vyn begriplig utan ett externt tilelager.



## UX-paritet: ÖST som del av Loppanalys-familjen

ÖST behåller sin varma kust-, vår- och skogsidentitet, men använder samma arbetsmönster som Ultravasan och Gotaleden: en panoramisk, låg hero med tydlig individuell sökning; separata individ- och kartduellingångar; sammanhängande capability-styrd analys med sticky ankarnavigation; skannbara KPI-/analyskort; valbara könsserier; översikt före detaljer; och metodförklaring nära analysen utan att dominera den. Den aktuella hero-bilden ligger som fullbreddsbild med mörk vänstergradient och sökpanelen direkt under rubriken.

Familjekorten behåller fem distinkta bildmiljöer: kust för Ultra/Duo och inlandets bokskog/Verkeåmiljö för Trail 22/14/5. Ingen bild presenteras som en exakt vy av ett namngivet landmärke. Sökförslag ska kunna väljas med mus eller piltangenter/Enter och öppnar den källbaserade profilmodalen. Percentil- och sluttidsserier har synliga toggles, legend, antal och värden. Gruppfördelningar visar stapelöversikt först och full tabell vid behov.

Analysen fortsätter vara en scrollbar helhet: Översikt, Loppets dynamik, Delsträckor, Bana/Course Intelligence, Historisk översikt och Metod visas samtidigt när respektive capability finns. Resultatdatabas och Kartduell är avsiktliga arbetsvyer. Metodförklaringar och dataregler samlas i Metod; enskilda analyskort ger kort kontext via info-kontroll.
