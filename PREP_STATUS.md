# Förberedelsestatus

Datum: 2026-09-10  
Status: **DATA FÄRDIG / ENGINE-HANDOFF-READY**

ÖST-repot är nu förberett så långt det är meningsfullt innan den generiska Gotaleden-kärnan är färdig. Full resultatinhämtning, råarkivering, datakvalitetskontroll, kuratering, Duo-normalisering och engine-readiness är genomförda. Kvarvarande punkter kräver antingen den färdigrefaktorerade analysmotorn eller nytt/verifierat källunderlag.

## Klart

- Projektomfattning 2018–2026 definierad, med 2020 och 2021 explicit `cancelled`.
- Fem tävlingsfamiljer: `ultra60`, `duo60`, `trail22`, `trail14`, `trail5`.
- Samtliga 34 genomförda år×familj-instansers Sportstiming-event-/distance-ID:n katalogiserade.
- **Full Sportstiming-import 2018–2026 genomförd och fryst** i `data/archive/ost-results-2018-2026.sqlite.gz`.
- Fryst arkiv granskat med separat audit: 9 871 resultat, 5 382 ursprungliga splits, 0 källfel och SQLite integrity `ok`.
- Audit har inga dubblettnycklar, orphan-splits, negativa/omkastade splits eller finishers utan sluttid.
- 2 024 individuella Ultra-resultat har slut-split/sluttid verifierad utan avvikelse över två sekunder.
- **Kuraterad engine-databas byggd** i `data/derived/ost-analysis-2018-2026.sqlite.gz`.
- Kuraterad databas: 9 871 resultat, 9 571 individuella deltagarposter, 300 Duo-lag, 599 publicerade Duo-medlemsrader, 6 123 riktiga splitpassager och 699 härledda mått.
- Statuslagret förbättrat endast med explicit källbevis: 9 518 `FINISHED`, 332 `DNF`, 21 `UNKNOWN`; inga statuskonflikter.
- Startnummer återvunnet från Sportstimings exakta listkolumn `Startnr.` där detaljnormaliseringen saknade det: **100 % bib-täckning, 9 871/9 871**.
- Klubb och land kan säkert falla tillbaka på den frysta resultatraden; land finns för 9 571/9 571 individuella resultatrader.
- 2022 års individuella `Kategori`-fält (`F40-44`, `M45-49` osv.) används som explicit källa för kön och åldersklass, men aldrig för syntetisk exakt ålder.
- 2024–2026 har nästan komplett exakt kön/ålder i de publika detaljsidorna. 2018/2019/2023 lämnas utan kön/ålder där källan inte visar det.
- Ultra 60-splitstruktur verifierad och importerad för samtliga genomförda år.
- Duo team-splits parserade från de frysta teamdetaljerna: **741 splitpassager** utöver de individuella Ultra-splitsen.
- Duo-medlemsstruktur parserad: 599 medlemsrader. `source_sequence` bevaras; `leg_no` lämnas NULL eftersom källbevis inte räcker för generell etapptilldelning.
- Årsspecifik checkpoint-normalisering skapad.
- Bengtemölla 2022/2023 dubbel timing analyserad. `32 km` och `Bengtemölla` hålls separata; gapet är en **service-window candidate**, inte bevisad stationstid.
- Historiska Trace de Trail-referenser och geometrier analyserade utan automatisk återpublicering av tredjepartskoordinater.
- Ultra-course versions tilldelade för 2018, 2019, 2022–2023, 2024 och 2025–2026.
- Trail 21/22-course versions tilldelade för 2019, 2022–2024 och 2025–2026; 2018 hålls oassignad på grund av provenance-mismatch.
- Arrangörs-GPX lokalt arkiverad för Ultra 2024 och 2025/2026.
- Source registry, source coverage, capability policy, analysis-data-contract och engine-adapter finns.
- `reports/engine-readiness.json` byggs från den kuraterade databasen. Nuvarande läge: 13 race-instansers splitanalys är dataklar, 6 har även den lokala ruttgeometri som krävs för replay/kartduell, och 19 har verifierad course version.
- GitHub Actions finns för import/audit, kuraterad databas, semantik/status/identitetsprofilering, geometri, source coverage, readiness och foundation validation.
- GitHub Pages-placeholder finns i `docs/`.

## Primär handoff till analysmotorn

Den framtida Gotaleden-baserade motorn ska i första hand läsa:

`data/derived/ost-analysis-2018-2026.sqlite.gz`

Den frysta databasen i `data/archive/` är källbevis och rebuild-underlag, inte den normala frontend-inputen. Det finns **ingen anledning att hämta om Sportstiming 2018–2026** för att börja motorintegrationen.

Läs även:

1. `config/foundation-state.json`
2. `config/engine-adapter.json`
3. `reports/engine-readiness.md`
4. `research/gotaleden-engine-handoff.md`
5. `config/course-versions.json`
6. `config/checkpoint-normalization.json`

## Verkligt kvarvarande / medvetet uppskjutet

- **Generisk Gotaleden-core-integration:** väntar avsiktligt tills den pågående generiska refaktoreringen är färdig.
- **Historiska lokala route assets:** äldre Ultra och Trail 21/22 har jämförbarhetsbevis men saknar i flera fall lokalt återanvändningsmässigt lämplig GPX för karta/replay.
- **Trail 13/14 och Trail 5 course versions:** komplett verifierad historisk geometri saknas.
- **Trail 21/22 2018:** kandidatspåret är geometriskt starkt kompatibelt med 2019 men metadata anger 2016; formell tilldelning kräver årsspecifik proveniens.
- **Duo etappnummer:** medlemmarna är importerade men tillgänglig evidens bevisar inte att medlemsrad 1/2 alltid betyder etapp 1/2.
- **Cross-year personidentitet:** repeat-runner-funktion ska byggas som ett separat linkage-lager med confidence/evidence; namnlikhet får inte skriva över source-local identity.
- **Historiska kön/ålder:** 2018, 2019 och 2023 saknar tillräckligt explicit publicerad information i den frysta källan.
- **Fysisk Bengtemölla-tolkning:** approach/utpassage-hypotesen är plausibel men inte officiellt verifierad.

## Slutlig handoff-regel

Förberedelsefasen betraktas som avslutad när foundation-validatorn är grön på denna version av `main`. Därefter ska nästa utvecklingssteg vara adapter/integration mot den färdigrefaktorerade Gotaleden-kärnan — inte ny Sportstiming-import, ny banförstudie eller parallell frontend-fork.

När Gotaleden-kärnan är färdig ska arbetet alltså börja med **adapter/integration mot den redan färdiga kuraterade ÖST-datan**, inte med en ny förstudie eller ny resultatimport.
