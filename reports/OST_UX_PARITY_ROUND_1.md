# ÖST UX-paritet – förbättringsrunda 1

Datum: 2026-09-28  
Branch: `improve/ost-ux-parity`  
Jämförelsereferenser: aktuell frontend i `ultravasan-analys` och `gotaleden-splits`

## Syfte och avgränsning

Rundan höjer presentation, interaktion och analytisk läsbarhet utan att ändra source data, Engine 1.0-kontraktet, frysta totaler, proveniens eller capability-regler. Referensprodukterna har jämförts område för område i sina faktiska frontendfiler och renderade ytor. ÖST behåller sin befintliga modulstruktur och progressiva dataladdning.

## Parity-audit

| Område | Gap före rundan | Genomförd förbättring |
|---|---|---|
| Hero och identitet | Ren men tunn, generisk tvåkolumnsyta | Rik kust–vår–slott-komposition, tydligare ruttberättelse, blomning, lager, destination, premium-CTA och starkare typografisk hierarki |
| Produktsystem | Kort och filter saknade sammanhållen identitet | ÖST-färger, redaktionella ingresser, accentlinjer, mjukare ytor, tydligare aktiva tillstånd och konsekventa badges genom analysen |
| Analys- och scrollarkitektur | Varje navigationsval ersatte hela analysytan via `state.section` | Översikt, Loppets dynamik, Delsträckor, Bana / Course Intelligence, Historisk översikt och Metod renderas capability-styrt i samma långscrollade dokument. Sticky navigation använder fokuserbara ankare och hashbaserade deep links; Back/Forward återställer rätt sektion. Resultat och Jämför är fortsatt separata specialvyer. |
| Klubb och ort | Fritextfilter utan förslag | Datadriven combobox med tomt startläge, etiketterade förslag, tangentbordsnavigering, aktivt alternativ och tydligt tomläge |
| Könsuppdelning | En tabell i fältdynamik | Total, kvinnor och män i målgångsdiagram och percentiler; separata KPI:er och status; segmentmedianer per kön; kvinnor, män och täckning i historiken |
| Löpar-/lagval | Första åtta resultat visades före sökning | Neutralt startläge; förslag visas först efter aktiv sökning och förklarar namn, nummer och klass |
| Direktjämförelse | Rubrik, ett gap och två tabeller | Två tydliga deltagarkort, centralt sluttidsgap, bättre hierarki, separata passage- och delsträckekort samt förklarande gapnotation |
| Tom- och begränsningslägen | Korrekt men visuellt återhållsamt | Samma capability-budskap ligger kvar och får tydligare kort, badges och placerad hjälptext |
| Responsivitet och tillgänglighet | Fungerande bas | Nya komponenter har mobillägen, dokumentet håller viewporten, comboboxen stöder piltangenter/Enter/Escape och kön kodas med text samt färg |

## Slutrunda mot den faktiska profilbilden

`research/ost-grafisk-profil.png` inspekterades i originalupplösning före denna designpassning. Referensens tydligaste egenskaper är den fotografiska strandstigen med löpare, blommande förgrund, hav och kusthöjd, det redaktionella blå/guld-språket, bildbärande loppkort och en sammanhängande resa från kust mot inland.

Detta omsattes i produkten genom:

- en separat textfri kustbild med löpare, hav, sandstig och vårblomning,
- fem skilda bildmiljöer på loppfamiljernas kort: kust för Ultra, två löpare och kust/inland för Duo, bäck och bokskog för Trail 22 samt egna inlandsskogar för Trail 14 och Trail 5,
- en redaktionell miljöresa från hav via fiskeläge, kusthöjd, strand, ådal och backar till slott,
- tydlig märkning att miljöresan inte är tidtagningspunkter eller exakt banmodell,
- ett rikare profilhuvud för löpare och lag,
- fortsatt återhållsamma data- och diagramytor under den identitetsbärande toppen.

Referensbildens inbakade resultat, porträtt, exakta kartlinje och byggnadsmotiv har inte återanvänts som data eller verklighetsanspråk. Familjebilderna gör inga anspråk på att visa Bengtemölla, Hallamölla eller Christinehof exakt. Den två byte stora fil som råkade skapas vid namnbytet på `main` ersätts i denna branch med den verkliga 3,48 MB-referensbilden och normaliseras till `research/ost-grafisk-profil.png`.

## Verklig scrollarkitektur

Analysnavigationens sex huvudval är nu ankare i ett gemensamt dokument. Alla tillgängliga huvudsektioner finns samtidigt i DOM:en och filter eller enhetsbyte uppdaterar hela analysberättelsen. Delsträckor utelämnas för finish-only-upplagor och Bana / Course Intelligence utelämnas när banunderlag saknas. Ett ankare som `#segments` återställer sektionen, flyttar scrollpositionen och sätter tangentbordsfokus. Browser Back/Forward går mellan ankarhistoriken. Resultatdatabasen och Direktjämförelse/Kartduell renderas fortfarande som egna arbetsvyer eftersom de har annan uppgiftsstruktur.

## Analytisk hantering av kön

Könsserier skapas endast från källstödda `F`/`M`-värden. Totalen behåller alla resultat. Saknat kön lämnas saknat och redovisas genom täckningstext. När användaren väljer ett specifikt kön ersätter det filtrerade urvalet den jämförande uppdelningen. Gruppmedianer följer befintliga miniminivåer; segmentmedian visas först vid minst fem kompletta observationer.

## Medvetet kvarstående skillnader

- ÖST får ingen personhistorik över år eftersom verifierad identitetskoppling saknas.
- Äldre eller kortare lopp får inte replay, segment eller rutt bara för att referensprodukterna har motsvarande komponent.
- Duo redovisas fortsatt som lagobservationer; publiceringsordning görs inte om till etappnummer.
- Historisk prestationsjämförelse förblir låst till verifierad CourseVersion eller uttrycklig jämförelsegrupp.
- Avancerade analyser som kräver tätare passager visas inte för finish-only-upplagor.

Dessa punkter är datagränser, inte återstående UX-skuld.

## Validering

Regressionen täcker könslegend, klubb/ort-comboboxens tangentbordsflöde, neutralt jämförelseval och den uppgraderade Direktjämförelsen. Slutversionen passerar 22 Python-tester, 17 JavaScript-tester och samtliga browserflöden utan konsol-, sid- eller oväntade nätverksfel.

Den kritiska kod- och dataöverföringen mäts till 67 770 byte gzip. Den nya WebP-bilden är 287 096 byte; även om den räknas in blir första visuella laddningen cirka 355 KB. Bootstrap plus största valda racepaket är 32 383 byte gzip. Progressiv laddning, lokala vendor-filer och lazy route/replay ligger kvar.
