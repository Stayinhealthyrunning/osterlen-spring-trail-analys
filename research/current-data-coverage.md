# Aktuell datatäckning

Senast uppdaterad: 2026-09-10

## Officiella resultat

Sportstiming-event är katalogiserade för samtliga genomförda analysår: 2018, 2019, 2022, 2023, 2024, 2025 och 2026. Event-ID:n är verifierade mot Österlen Spring Trails officiella resultatarkiv. Distans-/klass-ID:n har också inventerats från den publika Sportstiming-strukturen.

## Mellantider och deltagardetaljer

Representativa individuella resultatsidor visar split-tabell för Ultra 60 samtliga genomförda år:

| År | Observerade källrader |
|---:|---|
| 2018 | Stenshuvud km 14; Bengtemölla km 32; Vantalängan km 52; Finish |
| 2019 | Stenshuvud km 14; Bengtemölla km 32; Vantalängan km 52; Finish Km 60+ |
| 2022 | 32 km; Bengtemölla; 62 km |
| 2023 | 32 km; Bengtemölla; 62 km |
| 2024 | 34 km; 60 km |
| 2025 | 34 km; 60 km |
| 2026 | 34 km; 60 km |

För Trail 21/22, Trail 13/14 och Trail 5 har ingen split-tabell observerats i nuvarande representativa prover. Detta ska tolkas konservativt: det bevisar schemafrånvaro i de testade deltagardetaljerna, inte universell frånvaro av all möjlig extra timingdata.

Duo-resultatklassen finns 2019 och 2022–2026, men individuella resultatlänkar kan inte användas på samma sätt. En team/relay-adapter krävs.

## Bengtemölla 2022–2023

Sportstiming redovisar både `32 km` och `Bengtemölla`, med 100 m/0,1 km som källsegment. I ett aggregat av 60 giltiga deltagarpar per år är medianintervallet:

- 2022: 255 sekunder.
- 2023: 142,5 sekunder.

Det är för långt och variabelt för att behandla raderna som två rena duplicerade mätningar av samma passage. `Bengtemölla` används därför som kanonisk namngiven checkpoint och `32 km` bevaras separat. Arbetshypotesen är approach/förvarning → service → utpassage, men matplaceringen är inte verifierad och gapet får endast kallas en service-window candidate.

## Arrangörsarkiverade filer i repot

Följande filer har hämtats direkt från Österlen Spring Trails webbplats via projektets GitHub Action:

- Ultra 60 GPX för 2024.
- Ultra 60 GPX som används som arrangörsrutt för 2025/2026.
- Ultra 60-karta PDF för 2025/2026.
- Trail 21-karta PDF från 2019.

Varje nedladdad fil har SHA-256-kontrollsumma och proveniensmetadata.

## Historisk bangeometri

Trace de Trail-referenser finns katalogiserade för Ultra 60 och Trail 21/22 för samtliga genomförda år i scope. Den publika kartgeometrin har analyserats transient och används för fingeravtryck, längd, landmark-projektion och cross-year corridor comparison. Full koordinatserie lagras inte som återpublicerad tredjepartsrutt.

Aktuell course-versionmodell:

### Ultra 60

- 2018: `ultra60-2018` – separat historisk version, ca 62,055 km beräknad kartgeometri.
- 2019: `ultra60-2019` – separat fingerprint, starkt kompatibel med 2022/23.
- 2022–2023: `ultra60-2022-2023` – exakt samma publika geometri.
- 2024: `ultra60-2024` – materiellt förändrad bana, lokal arrangörs-GPX finns.
- 2025–2026: `ultra60-2025-2026` – samma arrangörsruttkälla och 100 % corridor overlap inom 50 m i den publika geometrin; lokal arrangörs-GPX finns.

### Trail 21/22

- 2018: ännu inte formellt tilldelad. Kandidat Trace 7897 är geometriskt mycket nära 2019 men har `dateCompet=16/04/2016`.
- 2019: `trail22-2019`.
- 2022–2024: `trail22-2022-2024` – exakt samma publika geometri.
- 2025–2026: `trail22-2025-2026` – exakt samma publika geometri och mycket starkt kompatibel med 2024.

### Trail 13/14 och Trail 5

År-för-år course versions är fortfarande öppna eftersom en komplett verifierad historisk geometri inte har säkrats.

## Vad som återstår av datainsamlingen

- Produktionsimport av samtliga Sportstiming-resultat och deltagardetaljer med råsnapshot/proveniens.
- Duo lag-/medlemsadapter.
- Fler lokala/redistributerbara historiska ruttfiler där karta/replay kräver det.
- Historisk geometri för Trail 13/14 och Trail 5.
- Årsspecifik proveniens för 2018 Trail 21/22.

Dessa punkter är uppskjutna till implementationsfasen och blockerar inte att ÖST-grunden nu lämnas vilande.
