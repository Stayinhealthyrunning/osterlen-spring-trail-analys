# ÖST Splits – systemaudit och slutpolering 2026-09-29

## Slutsats

ÖST Splits har gåtts igenom från datakontrakt och statistik till interaktion, layout, responsivitet och referensparitet. Auditens kodändringar ligger i `polish/ost-system-audit` / PR #47 och bygger vidare på Engine 1.0 utan att ändra de frysta källarkiven.

Den sista fulla QA-körningen före denna rapport var grön på commit `a752b7cbf613262bb341845d91c6c14326799b8f`:

- `Validate ÖST foundation`: success.
- `ÖST Splits frontend`: success.
- 25 Python-tester: 25/25.
- 25 JavaScript-tester: 25/25.
- 18 browserflöden: samtliga passerade.
- Samtliga 34 tävlingsupplagor renderades och capability-gating verifierades i Chromium.
- 1536×1024, 1366×768, 900×900 och 390×844 verifierades utan dokumentöverflöde.
- Inga oväntade console-, page- eller network-fel.
- Reduced-motion, tangentbordsnavigering, dialoger, Replay och fallback vid karttiles testades.

PR #47 är fortfarande draft och är inte mergad eller produktionsdeployad av denna audit.

## Data och statistisk integritet

Källomfattningen är oförändrad: 34 genomförda race-instanser, 9 871 resultat, 6 123 observerade mellantidspassager, 300 Duo-lag och 599 publicerade lagmedlemsrader. Full Engine-export är 5 417 501 byte rå / 450 542 byte gzip.

Auditen kontrollerar nu maskinellt varje exporterad resultat- och splitrad. FINISHED måste ha positiv sluttid, placeringar måste vara positiva när de finns, ålder måste ligga inom rimligt intervall när exakt ålder publicerats, varje split måste höra till ett existerande resultat och en existerande checkpoint, och en fullföljares split kan inte ligga efter sluttiden. Duo-medlemmar måste höra till ett existerande lag och `leg_no` förblir null när etapptilldelning inte är verifierad.

En konkret historisk ordningsrisk upptäcktes och korrigerades: 2019 Ultra/Duo kunde tidigare få semantisk checkpointordning från rå gruppering i stället för den dokumenterade analysordningen. Exporten följer nu explicit checkpoint-policy: Start → Stenshuvud → Bengtemölla → Vantalängan → Mål. Regressionstest finns både på Engine-export och frontend.

Små underlag hanteras konsekvent: median publiceras från n ≥ 5, Q25–Q75 från n ≥ 10 och Q10–Q90 från n ≥ 20. Även översiktens median-KPI följer nu n ≥ 5. Null omvandlas aldrig till noll.

Historiska upplagor där segmentdistans saknas visar nu tidsbaserad median och tidsbaserad spridning i stället för meningslösa tomma fartfält. Fart visas bara där rapporterad segmentdistans finns.

Höjddata får inte längre skapa falsk D+/D− över luckor. Terrängmått kräver tillräckligt komplett höjdprofil och kedjan bryts vid saknade höjdvärden. Rekonstruerad Trail 5-rutt och historiska rutter behåller sin proveniens; ofullständig eller saknad höjd redovisas som saknad i stället för att fyllas ut.

## Könsuppdelning

Kvinnor och män separeras när källan faktiskt stöder kön och när analysen är meningsfull. Ingen könsinferens görs från namn.

Följande är könsuppdelat eller könsmedvetet där data finns:

- sluttidsfördelning,
- percentiltrösklar,
- startande/fullföljare/brytare/startade inte,
- median och fullföljandegrad,
- DNF:s sista observerade kontroll,
- median per delsträcka,
- starkast avslutning,
- historik över startande/fullföljande,
- kvinnorepresentation i årets historiska fingeravtryck,
- placement scatter.

Aktivt könsfilter ersätter parallell kvinna/man-serie med vald grupp. Historiska år med saknat kön visas som saknade, aldrig som noll. Historisk könstabell kräver minst 80 % källstödd könstäckning bland faktiska startande.

Duo behandlas som lag. Teamkön härleds inte från medlemmar.

## Interaktion och navigation

Huvudanalysen är ett sammanhängande scroll-dokument: Översikt → Loppets dynamik → Delsträckor när de finns → Bana → Historik → Metod. Sticky navigation fungerar som ankarnavigation och använder `aria-current="location"`. Resultatdatabas och Jämför är medvetet separata arbetsvyer.

Kontrollerade interaktioner:

- racefamilj och år,
- min/km ↔ km/h,
- kön, klass, status och klubb/ort,
- klubb/ort-autocomplete med tangentbord,
- global sökning och resultatdatabassökning,
- resultatsortering och paginering,
- profil via klick och tangentbord,
- lokala favoriter,
- delsträcksval,
- måltempo/loppplan,
- karta och höjd,
- Runner Replay,
- Direktjämförelse,
- Kartduell,
- browser back/forward och djupa länkar.

Jämförelseväljaren är tom tills användaren söker. Upplagor utan verifierad replay/rutt tillåter exakt två val för Direktjämförelse och erbjuder inte en falsk 3–5-personers Kartduell. Replay-klara upplagor tillåter 2–5.

Karttile-fel testas explicit. Analysen fortsätter då i neutral ruttvy utan att tappa loppdata.

## Löpardetalj och Direktjämförelse

Profilen visar källstödd status, sluttid, placering, klass, klubb/ort, demografi när den finns samt verkliga passager. För segmentupplagor finns nu också deltagarens delsträckor relativt hela upplagans fältmedian. Saknad passage eller placering fylls aldrig ut.

Direktjämförelsen har harmoniserats visuellt och informationsmässigt: två lika deltagarkort, central sluttidsskillnad, kompakta passage-/delsträckstabeller och observerade insikter om gemensamma passager, ledningsväxlingar, största observerade lucka och närmaste passage. Den fungerar även på 390 px utan dokumentöverflöde.

## Layout, typografi och visuellt flöde

Manuell screenshotgranskning genomfördes för hela den långa desktopsidan och för mobil, Trail 5-bana, Duo-profil och Direktjämförelse.

Följande polerades:

- första sidans två analyskort har samma höjd,
- rubrikhierarki och sektionsavstånd har en konsekvent rytm,
- sidans övergångar mellan översikt, dynamik, segment, bana, historik och metod är tydliga,
- täta klubb- och ålderslistor visar prioriterad del direkt och behåller hela källistan utfällbar,
- jämförelsetabeller har reducerats till rimlig kolumnbredd,
- kart- och terrängkort duplicerar inte varningar,
- tekniska statuskoder har svenska presentationsetiketter,
- diagram har textlegend och använder inte färg som enda kodning,
- mobilens dialoger och jämförelsekort ligger inom viewport,
- internt breda diagram använder kontrollerad horisontell scroll utan att skapa document overflow.

Hero, distanskort och Österlen-resan behåller ÖST:s egna grafiska profil och ska inte göras till en recolor av referensverktygen.

## Paritet mot Gotaleden och Ultravasan

Funktioner som är relevanta och källmässigt möjliga i ÖST finns nu representerade:

| Referensfunktion | ÖST-status |
|---|---|
| Målgångsfördelning och percentiler | Implementerat |
| Kvinna/man-serier | Implementerat med källtäckningsregler |
| Placement exploration | Implementerat som interaktiv sluttid–totalplacering |
| Status / DNF-fältflöde | Implementerat konservativt från verkliga passager |
| Delsträckor, spridning, retention, placeringsrörelse | Implementerat där splitdata finns |
| Klass- och klubb/ort-analys | Implementerat |
| Profil med relativ prestationskontext | Implementerat; segment mot fältmedian |
| Måltempo/loppplan | Implementerat |
| Course Intelligence / bana och proveniens | Implementerat utan syntetisk svårighetsscore |
| Runner Replay | Implementerat bara där lokal rutt + verkliga passager finns |
| Head-to-head / Direktjämförelse | Implementerat |
| Kartduell | Implementerat där replay-capability finns |
| Favoriter | Implementerat lokalt |
| Historik och banjämförbarhet | Implementerat med explicit course-gating |
| Metod/data-quality guide | Implementerat |
| Responsive/accessibility/reduced motion | Implementerat och browsertestat |

Funktioner från referenserna som **inte** ska kopieras till ÖST utan starkare underlag:

- personhistorik/Hall of Fame över år – verifierad cross-year-identitet saknas,
- member→leg-analys för Duo – etapptilldelningen är inte verifierad,
- Replay för Trail 22/14/5 – mellantidsunderlag saknas,
- historisk ruttvisualisering där lokal publicerbar rutt saknas,
- syntetisk sammanvägd difficulty score,
- klassutveckling som förutsätter stabil normalisering över år när källklassernas semantik inte är verifierad för sådan användning.

Detta är avsiktlig capability-gating, inte funktionsluckor som ska fyllas med antaganden.

## Prestanda

Senaste fulla gröna frontendkörningen före rapporten:

| Mått | Uppmätt | Budget |
|---|---:|---:|
| Bootstrap gzip | 2 049 B | 10 240 B |
| Största racebundle gzip | 29 234 B | 76 800 B |
| Bootstrap + största racebundle | 31 283 B | 102 400 B |
| Största racebundle rå | 329 247 B | 614 400 B |
| Full Engine gzip | 450 542 B | 768 000 B |
| HTML gzip | 2 989 B | 32 768 B |
| CSS gzip | 8 633 B | 76 800 B |
| Initial JavaScript gzip | 32 323 B | 262 144 B |
| Kritisk initial transfer gzip | 76 322 B | 524 288 B |

Rutt, höjd, replay och kartvendor förblir lazy-loadade. Historiken levereras som liten aggregerad fil, inte genom hydrering av alla 9 871 resultat.

## Kvarstående avsiktliga begränsningar

ÖST ska fortsatt hellre visa mindre än att konstruera data. Följande är därför bindande:

1. ingen köns-, ålders- eller personidentitetsinferens,
2. ingen Duo member→leg-inferens,
3. ingen syntetisk split eller Replay,
4. ingen lånad bana från annan upplaga,
5. ingen falsk D+/D− över saknad höjd,
6. ingen prestationshistorik över banor som inte uttryckligen är jämförbara,
7. 32 km och Bengtemölla 2022/2023 hålls som separata observationer,
8. Trail 14 och Trail 5 behåller tydlig rekonstruktions/proveniensmärkning.

## Release gate

Tekniskt releasevillkor för PR #47 är:

- foundation green,
- Python green,
- JavaScript green,
- browser-QA green,
- performance budget green,
- ingen ny provenance- eller capability-regression,
- sista visuella screenshotkontroll utan blockerande avvikelse.

När dessa villkor är gröna kan PR #47 markeras ready for review. Merge och produktionsdeploy är separata beslut.
