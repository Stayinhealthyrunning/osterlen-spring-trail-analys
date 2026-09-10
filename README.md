# Österlen Spring Trail Analys

Interaktiv analys av Österlen Spring Trail – resultat, banor, pacing och loppets utveckling från 2018 och framåt.

## Projektstatus

**Datagrunden är färdig och redo för integration mot den generiska Gotaleden-motorn.**

Repot innehåller inte bara förstudie/kataloger utan en komplett fryst Sportstiming-import för alla genomförda analysår 2018–2026, en separat auditerad och kuraterad analysdatabas, Duo-team/splits/medlemsrader, checkpointsemantik, banversionsmodell och en maskinläsbar readiness-matris.

Den generiska Gotaleden-frontenden är fortfarande **medvetet inte kopierad**. När Gotaleden-refaktoreringen är färdig ska ÖST anslutas via konfiguration/adaptrar till den färdiga kärnan, inte bli en parallell hårdkodad fork.

Primär framtida engine-input:

`data/derived/ost-analysis-2018-2026.sqlite.gz`

Den immutabla källkopian finns i:

`data/archive/ost-results-2018-2026.sqlite.gz`

## Omfattning

Analysperioden börjar 2018. Genomförda upplagor i scope är 2018, 2019, 2022, 2023, 2024, 2025 och 2026. Åren 2020 och 2021 registreras explicit som inställda och får aldrig tolkas som saknad resultatdata.

Banfamiljer:

- `ultra60` – individuella ultraloppet.
- `duo60` – lag på samma fulla geometri som `ultra60` respektive år.
- `trail22` – historiskt marknadsförd som 21 km, senare 22 km.
- `trail14` – historiskt marknadsförd som 13 km, senare 14 km.
- `trail5` – 5 km.

## Resultatarkiv och datakvalitet

Sportstiming är officiell result source of record för samtliga genomförda analysår. Den fulla importerade källan innehåller **34 race-år-instansers 9 871 resultat** och är fryst tillsammans med provenance och checksummor.

Den separata audit-kedjan verifierar bland annat:

- SQLite integrity `ok`.
- 34/34 förväntade importer och 0 källfel.
- Inga dubblettnycklar eller trasiga resultat-ID:n.
- Inga orphan-splits, negativa splits eller kronologifel.
- Inga finishers utan positiv sluttid.
- 2 024 Ultra-resultat där sista split/sluttid kan kontrolleras utan en enda avvikelse över två sekunder.

Den kuraterade analysdatabasen innehåller:

- **9 871 resultat**.
- **9 571 individuella deltagarresultat**.
- **300 Duo-lag**.
- **599 publicerade Duo-medlemsrader**.
- **6 123 verkliga splitpassager**, varav 741 från Duo-teamdetaljer.
- **699 härledda checkpointmått**.
- Status: **9 518 FINISHED, 332 DNF, 21 UNKNOWN**.

332 poster som först lämnades `UNKNOWN` har uppgraderats till `DNF` endast eftersom samma explicita källstatus finns i den frysta Sportstiming-datan. De sista 21 lämnas `UNKNOWN` i stället för att gissas.

## Fälttäckning

Efter en separat offline-profil av den frysta källan återvinns säkra listfält där detaljsidan saknar dem:

- Startnummer: **9 871/9 871** resultat.
- Land: **9 571/9 571** individuella resultat.
- 2022 har i princip full köns-/åldersklasstäckning genom explicit `Kategori` (`F40-44`, `M45-49` osv.). Exakt ålder härleds aldrig från ett intervall.
- 2024–2026 har nästan komplett exakt kön och ålder från Sportstimings publika detaljsidor.
- 2018, 2019 och 2023 saknar motsvarande tillförlitligt publicerade kön/ålder i den frysta strukturen och lämnas därför utan inferens.

## Splits och Duo

Individuella Ultra 60-resultat har följande verifierade timingstruktur:

- 2018–2019: Stenshuvud, Bengtemölla, Vantalängan och mål.
- 2022–2023: `32 km`, `Bengtemölla` och mål/`62 km`.
- 2024–2026: `34 km` och mål/`60 km`.

Duo är också normaliserat från de frysta teamdetaljerna och har verkliga team-splits för samtliga Duo-år. Nästan alla lag har två publicerade medlemsrader; totalt finns 599 medlemsrader. Deras `source_sequence` bevaras, men `leg_no` lämnas NULL eftersom tillgänglig evidens inte räcker för att bevisa att radordningen alltid motsvarar etapp 1/2.

För Trail 21/22, Trail 13/14 och Trail 5 hittades ingen intermediate split-tabell i den kompletta importerade publika resultatmängden. Resultat-/finishanalyser kan användas, men split/replay får inte syntetiseras.

## Bengtemölla 2022–2023

Sportstiming visar två separata observationer: först `32 km`, därefter `Bengtemölla`, trots ett angivet källsegment på endast 0,1 km/100 m. Aggregatanalys visar ett betydligt längre och varierande tidsintervall.

Arbetshypotesen är att `32 km` kan vara approach/förvarning och `Bengtemölla` en senare observation i samband med stationen. Den fysiska matplaceringen är inte verifierad. Råobservationerna hålls därför separata och gapet får endast beskrivas som en **service-window candidate**, inte säker stationstid.

## Banversioner och historisk jämförbarhet

Marknadsförd distans är separerad från faktisk bangeometri. `config/course-versions.json` är source of truth för banversionerna.

Ultra 60:

- 2018 är en egen, tydligt längre version.
- 2019 är separat men starkt geometriskt kompatibel med 2022–2023.
- 2022 och 2023 har exakt samma publika kartgeometri.
- 2024 är en materiellt förändrad bana och har arrangörs-GPX arkiverad lokalt.
- 2025 och 2026 använder samma arrangörsruttkälla och praktiska korridor/längd; arrangörs-GPX är arkiverad lokalt.

Trail 21/22:

- 2019 är separat men starkt kompatibel med senare år.
- 2022–2024 har exakt samma publika kartgeometri.
- 2025–2026 har exakt samma publika kartgeometri och är mycket nära 2024.
- 2018-kandidaten är geometriskt nära 2019 men dess Trace-metadata är daterad 2016, så 2018 lämnas formellt oassignad tills årsspecifik proveniens finns.

Trail 13/14 och Trail 5 väntar fortfarande på tillräckligt komplett verifierad historisk geometri för course-versionering.

## Engine readiness

`reports/engine-readiness.json` beräknas direkt från den kuraterade databasen och styr vilka funktioner som faktiskt kan erbjudas.

Nuvarande dataläge:

- **13** race-instansers verkliga splits räcker för splitanalys.
- **6** race-instansers kombination av splits + lokal route asset räcker redan för replay/kartduell: Ultra och Duo 2024–2026.
- **19** race-instansers course version är verifierad.
- Kortare lopp utan splits får fortfarande resultat-, finish-, deltagar- och course-version-analyser där underlaget stödjer dem.

## Dataprinciper

- Rådata bevaras före normalisering.
- Saknade splits, placeringar, checkpointpassager, status, ålder, kön eller lagrelationer får aldrig fabriceras.
- Duo ärver respektive års Ultra 60-bana; benlängder får inte hårdkodas som 30+30 km.
- Cross-year-resultat ska respektera `course_version` och jämförbarhetsgrupper.
- En verifierad historisk kartgeometri betyder inte automatiskt att en redistributerbar lokal GPX finns för frontend/replay.
- Cross-year personidentitet är ett separat framtida confidence-lager; namnlikhet får inte ersätta source-local identity.

## Viktiga filer

- `config/foundation-state.json` – maskinläsbart aktuellt projektläge.
- `config/engine-adapter.json` – kontrakt för integration mot den generiska analysmotorn.
- `data/archive/ost-results-2018-2026.sqlite.gz` – immutabel fryst Sportstiming-källa.
- `data/derived/ost-analysis-2018-2026.sqlite.gz` – primär kuraterad engine-input.
- `reports/result-archive-audit.json` – djup audit av den frysta databasen.
- `reports/curated-analysis-db-summary.json` – kontrollsummering av analysdatabasen.
- `reports/engine-readiness.md` – faktisk funktions- och fälttäckning race för race.
- `reports/status-evidence-profile.json` – statusbevis för tidigare UNKNOWN-poster.
- `reports/identity-field-profile.md` – offline-inventering av publicerade fält.
- `config/course-versions.json` – verifierad banversionsmodell.
- `config/checkpoint-normalization.json` – årsspecifik timingsemantik.
- `research/gotaleden-engine-handoff.md` – instruktioner för nästa integrationsfas.

## Validering

Kör lokalt:

```bash
python tools/validate_foundation.py
```

GitHub Action `Validate ÖST foundation` kör samma konsistenskontroll automatiskt.

## Nästa fas

När Gotaleden-kärnans generiska refaktorering är färdig ska arbetet börja med adapter/integration mot `data/derived/ost-analysis-2018-2026.sqlite.gz`.

Det behövs **ingen ny ÖST-förstudie och ingen ny Sportstiming-import av 2018–2026** innan dess. Verkliga återstående källfrågor gäller främst historiska lokala banfiler, Trail 13/14 och 5 km-banversioner, Trail 21/22 år 2018, Duo-etappordning, historiska kön/åldersluckor och en separat metod för säker cross-year personmatchning.
