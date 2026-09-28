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
| Översikt och scrollflöde | Nyckeltal följdes av få kompakta paneler | Längre läsflöde med ingresser, könsdelad målgångsfördelning, percentilserier, könsperspektiv, klassdata och synlig metodguide |
| Klubb och ort | Fritextfilter utan förslag | Datadriven combobox med tomt startläge, etiketterade förslag, tangentbordsnavigering, aktivt alternativ och tydligt tomläge |
| Könsuppdelning | En tabell i fältdynamik | Total, kvinnor och män i målgångsdiagram och percentiler; separata KPI:er och status; segmentmedianer per kön; kvinnor, män och täckning i historiken |
| Löpar-/lagval | Första åtta resultat visades före sökning | Neutralt startläge; förslag visas först efter aktiv sökning och förklarar namn, nummer och klass |
| Direktjämförelse | Rubrik, ett gap och två tabeller | Två tydliga deltagarkort, centralt sluttidsgap, bättre hierarki, separata passage- och delsträckekort samt förklarande gapnotation |
| Tom- och begränsningslägen | Korrekt men visuellt återhållsamt | Samma capability-budskap ligger kvar och får tydligare kort, badges och placerad hjälptext |
| Responsivitet och tillgänglighet | Fungerande bas | Nya komponenter har mobillägen, dokumentet håller viewporten, comboboxen stöder piltangenter/Enter/Escape och kön kodas med text samt färg |

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

Den kritiska initiala överföringen mäts till 66 153 byte gzip. Bootstrap plus största valda racepaket är 32 383 byte gzip. Progressiv laddning, lokala vendor-filer och lazy route/replay ligger kvar.
