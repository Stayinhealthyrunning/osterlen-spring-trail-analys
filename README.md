# Österlen Spring Trail Analys

Interaktiv analys av Österlen Spring Trail – resultat, banor, pacing och loppets utveckling från 2018 och framåt.

## Projektstatus

Förberedelsegrunden är färdig för nästa fas. Repot innehåller nu tävlings-/årsmodell, Sportstiming-event och distans-ID:n, split-/trackinginventering, checkpoint-normalisering, banversionsmodell, geometrisk år-jämförelse, käll-/proveniensregler, analys-capability policy och ett uttryckligt datakontrakt mot den generiska Gotaleden-baserade analysmotorn.

Den generiska Gotaleden-frontenden är **medvetet inte kopierad ännu**. När Gotaleden-refaktoreringen är färdig ska ÖST integreras mot den färdiga kärnan via konfiguration/adaptrar, inte genom en parallell hårdkodad fork.

Maskinläsbar nulägesbild finns i `config/foundation-state.json`. Teknisk handoff finns i `research/gotaleden-engine-handoff.md`.

## Omfattning

Analysperioden börjar 2018, då den moderna tävlingsstrukturen etablerades. Genomförda upplagor i scope är 2018, 2019, 2022, 2023, 2024, 2025 och 2026. Åren 2020 och 2021 registreras som inställda och får aldrig tolkas som saknad resultatdata.

Banfamiljer:

- `ultra60` – individuella ultraloppet.
- `duo60` – tvåmannalag på samma fulla geometri som `ultra60` respektive år.
- `trail22` – historiskt marknadsförd som 21 km, senare 22 km.
- `trail14` – historiskt marknadsförd som 13 km, senare 14 km.
- `trail5` – 5 km.

## Sportstiming – vad som redan är kartlagt

Sportstiming är officiell result source of record för samtliga genomförda analysår. Event-ID:n, distans-/klass-ID:n och den publika resultatstrukturen är katalogiserade.

Representativa deltagarsidor visar mellantidstabell för Ultra 60 samtliga genomförda år:

- 2018–2019: Stenshuvud, Bengtemölla, Vantalängan och mål.
- 2022–2023: `32 km`, `Bengtemölla` och mål/`62 km`.
- 2024–2026: `34 km` och mål/`60 km`.

För Trail 21/22, Trail 13/14 och Trail 5 har ingen mellantidstabell observerats i de nuvarande representativa proverna. Det bevisar inte att ingen enskild extra timingdata kan finnas, men UI:n får inte anta splits där de inte är verifierade.

Duo-klassen finns publikt för 2019 och 2022–2026, men behöver en särskild team/relay-adapter eftersom lagresultaten inte följer samma individuella detaljlänksstruktur.

## Bengtemölla 2022–2023

Sportstiming visar två separata observationer: först `32 km`, därefter `Bengtemölla`, med källsegmentet angivet som endast 0,1 km/100 m. I 60-pars aggregat är medianintervallet ändå 255 sekunder 2022 och 142,5 sekunder 2023.

Arbetshypotesen är därför att `32 km` är en approach/förvarning och att `Bengtemölla` registreras när löparen lämnar stationen efter vätska/mat/service. Hypotesen är plausibel men inte fysiskt verifierad. Råobservationerna hålls därför separata; `Bengtemölla` är kanonisk namngiven checkpoint och gapet får endast beskrivas som en **service-window candidate**, inte säker stationstid.

## Banversioner och historisk jämförbarhet

Tävlingsnamn och marknadsförd distans är separerade från faktisk bangeometri. `config/course-versions.json` är den aktuella source-of-truth-modellen.

Ultra 60:

- 2018 är en egen, tydligt längre version.
- 2019 är separat men starkt geometriskt kompatibel med 2022–2023.
- 2022 och 2023 har exakt samma publika kartgeometri.
- 2024 är en materiellt förändrad bana och har arrangörs-GPX arkiverad lokalt.
- 2025 och 2026 använder samma arrangörskälla och samma praktiska korridor/längd; arrangörs-GPX är arkiverad lokalt.

Trail 21/22:

- 2019 är separat men starkt kompatibel med senare år.
- 2022–2024 har exakt samma publika kartgeometri.
- 2025–2026 har exakt samma publika kartgeometri och är mycket nära 2024.
- 2018-kandidaten är geometriskt mycket nära 2019 men har Trace-metadata daterad 2016; den lämnas därför formellt oassignad tills årsspecifik proveniens finns.

Trail 13/14 och Trail 5 väntar fortfarande på en tillräckligt komplett verifierad historisk geometri för course-versionering.

## Dataprinciper

- Rådata bevaras före normalisering.
- Saknade splits, placeringar, checkpointpassager, status eller lagrelationer får aldrig fabriceras.
- Duo ärver respektive års Ultra 60-bana; benlängder får inte hårdkodas som 30+30 km.
- Cross-year-resultat ska respektera `course_version` och jämförbarhetsgrupper.
- En verifierad historisk kartgeometri betyder inte automatiskt att en redistributerbar GPX-fil finns för frontend/replay.
- Trace de Trail-kartgeometri används transient för geometriska fingeravtryck och jämförelse; full tredjepartsgeometri återpubliceras inte automatiskt.

## Viktiga filer

- `config/foundation-state.json` – sammanfattar vad som är klart respektive uppskjutet.
- `config/race-editions.json` och `config/race-catalog.json` – år och tävlingsklasser.
- `config/course-versions.json` – verifierad banversionsmodell.
- `config/checkpoint-normalization.json` – årsspecifik timingsemantik.
- `config/analysis-data-contract.json` och `config/engine-adapter.json` – kontrakt mot analysmotorn.
- `data/source/sportstiming/` – event-, klass-, split- och trackinginventering.
- `reports/source-coverage.md` – faktisk funktionell datatäckning per år/familj.
- `reports/tracedetrail-public-geometry-analysis.md` – geometrisk banhistorik utan återpublicerad koordinatserie.
- `research/gotaleden-engine-handoff.md` – instruktion för framtida integration.

## Validering

Kör lokalt:

```bash
python tools/validate_foundation.py
```

GitHub Action `Validate ÖST foundation` kör samma konsistenskontroll automatiskt.

## Nästa fas när projektet återupptas

1. Integrera den färdigrefaktorerade generiska Gotaleden-kärnan enligt handoff/data contract.
2. Bygg produktionsimporten som hämtar och råarkiverar samtliga Sportstiming-resultatsidor/detaljer utan att förlora källfält.
3. Implementera Duo team/member-adapter.
4. Normalisera resultat/splits/checkpoints till motorkontraktet och låt capability-matrisen styra vilka analyser som aktiveras.
5. Komplettera lokala/redistributerbara historiska banfiler där det behövs för karta, höjdprofil och replay.

Det finns alltså ingen anledning att börja om med ÖST-förstudien när projektet tas upp igen.
