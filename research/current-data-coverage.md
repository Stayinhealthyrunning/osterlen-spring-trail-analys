# Aktuell datatäckning

Senast uppdaterad: 2026-09-27

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

Den fulla frysta importen bekräftar att Trail 21/22, Trail 13/14 och Trail 5 inte har någon importerad intermediate split-tabell i de publika resultatsidorna. De behandlas därför som finish/resultat-lopp i analysmotorn; splits eller replay får inte syntetiseras.

Duo-resultatklassen finns 2019 och 2022–2026. Teamdetaljer, verkliga team-splits och publicerade medlemsrader är nu parserade i den kuraterade databasen: 300 lag, 741 team-splitpassager och 599 medlemsrader. `source_sequence` bevaras; `leg_no` lämnas NULL tills uttrycklig källevidens kan verifiera etapptilldelningen.

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

- Trail 13/14: den tidigare 14,249 km rasterrekonstruktionen är superseded efter visuell kontroll. Nuvarande arbetsreferens är ett **13,472 km Hallamölla-splice-recept** baserat på verifierad Trail 21/22-geometri 2022–2024. Ingen redistributerbar lokal ruttfil betraktas som auktoritativ; äkta deltagar-/arrangörs-GPX är fortfarande målet.
- Trail 5: 2026 har en rekonstruerad referens på 5,481 km med oberoende full rasterkontroll på 5,545 km. Historisk exakt identitet är inte verifierad.

## Vad som återstår av datainsamlingen

Den fulla Sportstiming-importen, råarkivet, auditkedjan och Duo-adaptern är **klara**. Återstående källarbete är icke-blockerande förbättringar:

- autentisk deltagar-/arrangörs-GPX för Trail 13/14,
- autentisk Trail 5-GPX och historisk kortbanegometri,
- fler lokala/redistributerbara historiska ruttfiler där karta/replay kräver dem,
- årsspecifik proveniens för Trail 21/22 2018,
- uttryckligt källbevis för Duo-medlem → etapp,
- fysisk verifiering av Bengtemölla-timingens 2022/2023-matplacering.

Det stora bygget ska börja från den redan frysta och kuraterade databasen, inte med ny resultatskrapning.
