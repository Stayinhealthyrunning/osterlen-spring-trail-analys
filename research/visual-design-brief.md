# ÖST Splits – visuell designbrief

Datum: 2026-09-28  
Status: source of truth för produktens visuella uttryck

## Primär visuell referens

`research/OSt grafisk profil.png` ska inspekteras visuellt vid större designändringar. Bilden är primär referens för atmosfär, komposition, kust- och vårkänsla, redaktionell rikedom och resan från hav till slott. Den är ett koncept, inte en datakälla: inbakade exempelresultat, porträtt, kartlinjer och byggnadsbilder får inte kopieras som sakuppgifter.

Produktens heroasset `docs/assets/ost-coast-hero.webp` är en separat, textfri och icke platsidentifierande landskapsbild framtagen med referensen som stämnings- och kompositionsunderlag. Namngivna platser presenteras endast som text eller med verifierade visuella källor. Den redaktionella miljöresan skiljs uttryckligen från tidtagningspunkter och banversioner.

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

