# Förberedelsestatus

Datum: 2026-09-10  
Status: **GRUND FÄRDIG / HANDOFF-READY**

ÖST-repot är nu förberett så långt det är meningsfullt innan den generiska Gotaleden-kärnan är färdig. Kvarvarande punkter är inte blockerande för att pausa ÖST-arbetet; de hör till nästa implementationsfas eller kräver källor som ännu inte är verifierade/redistributerbara.

## Klart

- Projektomfattning och moderna analysår definierade: 2018–2026, med 2020 och 2021 explicit `cancelled`.
- Fem tävlingsfamiljer definierade: `ultra60`, `duo60`, `trail22`, `trail14`, `trail5`.
- Officiella Sportstiming-event-ID:n katalogiserade för samtliga genomförda år.
- Sportstiming distance/class-ID:n och publika resultatklasser kartlagda.
- Representativa deltagardetaljer inventerade år/familj.
- Ultra 60-splitstruktur verifierad för alla genomförda år; kortare distanser saknar split-tabell i de nuvarande proverna.
- Sportstiming tracking-/points-struktur inventerad.
- Duo identifierad som separat team/relay-adapterbehov.
- Årsspecifik checkpoint-normalisering skapad.
- Bengtemölla 2022/2023 dubbel timing analyserad på aggregat: 60 giltiga par/år, median 255 s respektive 142,5 s mellan `32 km` och `Bengtemölla`.
- Arbetshypotes dokumenterad: `32 km` är möjlig approach/förvarning och `Bengtemölla` möjlig utpassage efter service. Hypotesen är inte fysiskt verifierad och gapet får därför endast kallas service-window candidate.
- Historiska Trace de Trail-referenser katalogiserade för Ultra 60 och Trail 21/22.
- Publik Trace de Trail-kartgeometri analyserad transient utan att koordinatserier återpubliceras.
- Geometriska fingerprints, längder, start/mål och cross-year corridor overlap framtagna.
- Ultra-course versions tilldelade för 2018, 2019, 2022–2023, 2024 och 2025–2026.
- Trail 21/22-course versions tilldelade för 2019, 2022–2024 och 2025–2026; 2018 är explicit blockerad av provenance-mismatch i kandidatspåret.
- 2019 ↔ 2022/23 Ultra klassad som starkt kompatibel men inte identisk.
- 2022 = 2023 Ultra verifierad som exakt samma publika geometri.
- 2023 → 2024 Ultra verifierad som materiell banförändring.
- 2025 ↔ 2026 Ultra verifierad som samma praktiska korridor/längd och samma arrangörsruttkälla.
- Trail 21/22 verifierad som mycket stabil: 2022–2024 exakt samma publika geometri och 2025–2026 exakt samma publika geometri.
- Arrangörens Ultra 60-GPX för 2024 arkiverad med checksumma.
- Arrangörens gemensamma Ultra 60-GPX för 2025/2026 arkiverad med checksumma.
- Arrangörens Ultra 60-karta för 2025/2026 samt Trail 21-karta från 2019 arkiverade.
- Source registry, source coverage och analysis capability policy byggda.
- Maskinläsbart analysis-data-contract mot den generiska Gotaleden-motorn skapat.
- Engine-adapter-kontrakt och detaljerad Gotaleden-handoff dokumenterade.
- Automatisk foundation-validator skapad för att kontrollera år, familjer, Sportstiming-ID:n, course-versioner och grundläggande split-inventory-täckning.
- GitHub Actions finns för source discovery, Sportstiming-diagnostik, bangeometri, asset-hämtning, source coverage och foundation validation.
- GitHub Pages-placeholder finns i `docs/`.

## Medvetet uppskjutet till nästa fas

- **Full Sportstiming-resultatimport:** event-/klass-ID:n och struktur är kända; produktionshämtning av alla resultatsidor och råsnapshots byggs när analysmotorn ska matas på riktigt.
- **Duo team/member-adapter:** publika Duo-klasser är identifierade men lag-/medlemsstrukturen behöver en särskild normalisering.
- **Historiska lokala GPX-filer:** äldre Ultra och Trail 21/22 kan jämföras geometriskt via publika referenser, men karta/replay kräver lokala och återanvändningsmässigt lämpliga banfiler.
- **Trail 13/14 och Trail 5 course versions:** komplett verifierad historisk bangeometri saknas fortfarande.
- **Trail 21/22 2018:** kandidatspåret är geometriskt starkt kompatibelt med 2019 men metadata anger 2016; tilldelning väntar på årsspecifik proveniens.
- **Fysisk tolkning av Bengtemölla-mattorna:** hypotesen är starkt plausibel men ska inte göras till officiellt faktum utan arrangörs-/mattevidens.
- **Frontend/integration:** väntar avsiktligt tills Gotaleden-kärnans generiska refaktorering är färdig.

## När ÖST tas upp igen

Börja inte om med researchen. Läs i denna ordning:

1. `config/foundation-state.json`
2. `research/gotaleden-engine-handoff.md`
3. `config/analysis-data-contract.json`
4. `config/engine-adapter.json`
5. `config/course-versions.json`
6. `config/checkpoint-normalization.json`
7. `reports/source-coverage.md`

Kör därefter `python tools/validate_foundation.py` och gå direkt vidare med Gotaleden-core-integration och produktionsimport.
