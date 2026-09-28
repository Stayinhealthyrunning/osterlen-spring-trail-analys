# ÖST Splits – slutlig referensparitet mot Gotaleden och Ultravasan

Datum: 2026-09-28  
Referenser: `gotaleden-splits@bd9f2aa`, `ultravasan-analys@8d1ef31`  
ÖST-gren: `improve/ost-ux-parity`

## Slutsats

ÖST använder nu de delar från referensprodukterna som är generella, källstödda och relevanta för Österlen Spring Trail. Paritet betyder inte identiska skärmar: Engine 1.0 kräver capability-driven rendering, och funktioner som saknar verifierad identitet, passager eller publicerbar rutt ska inte simuleras.

| Område | Referensstyrka | ÖST efter revision | Beslut |
|---|---|---|---|
| Resultat, sök, sortering, filter | Gotaleden + UV | Sökbar/sorterbar databas, global sök, kön/klass/status, klubb/ort-autocomplete | Paritet |
| Könsanalys | Gotaleden + UV | Total + kvinnor + män i målgång, percentiler, status, segment och historik där täckning räcker | Paritet med strikt source coverage |
| Fältets utveckling | Gotaleden | Checkpointbaserat fältflöde, observerade passager, DNF-stopp och placeringsdata | Paritet |
| Runner/team profile | Båda | Profil, Journey, passager, delsträckor, relativ prestation, snittfart, favoriter, replay när capability finns | Paritet |
| Duo/team | Gotaleden | Lagserie + publicerade medlemmar utan fabricerad etapptilldelning | Engine 1.0-korrekt |
| Runner Replay | Båda | Samma rutt-/timingprincip, reduced motion, neutral kartfallback | Paritet |
| Kartduell | Gotaleden | 2–5 resultat, gemensam MapEngine, tile-failure fallback | Paritet |
| Direktjämförelse | Båda | Två resultat, checkpointtid/plats, segmenttid/fart/plats ±, gap och Kartduell | Paritet för samma RaceEdition |
| Segmentanalys | Båda | Median, Q25–Q75, Q10–Q90, fartretention, plats ±, DNF och könsserier | Paritet |
| Course Intelligence | Ultravasan | Rutt/höjd, valda segment, pacing/spread/DNF i segmentvyn, GPX-baserad D+/D− och loppplan | Paritet utan syntetiskt Difficulty-index |
| Måltempo/loppplan | Båda | Observerade segmentvikter, tydlig distansfallback, inga gissade resttider | Paritet |
| Historik | Ultravasan | Deltagande, jämförbar prestation, kön över tid, årets fingeravtryck, jämförbar toppnotering, inställda år som luckor | Paritet på eventnivå |
| Stark avslutning | Ultravasan | Källstödd sista-segment-placering, normaliserad mot startfält | Implementerad utan personidentitet |
| Metodik/UX | Ultravasan U8 | Guide nära toppen, aktivt lopp/dataskop/urval/filter, (i)-hjälp, keyboard, focus, reduced motion | Paritet |
| Visuell identitet | ÖST-specifik | Fotografisk kusthero, fem familjemiljöer, långscroll och platsberättelse | Medvetet rikare än referenserna |

## Medvetet inte porterat

- **Flerårig personhistorik, Flest lopp, Mest förbättrad och Jämnast:** kräver verifierad cross-year-identitet. ÖST saknar ännu denna evidens och namn får inte ersätta den.
- **Full historisk klubb/ort- och klassmatris:** nuvarande lilla historikpayload hålls avsiktligt kompakt. Current-edition gruppanalys finns; en full flerårsmatris skulle kräva on-demand historiska race bundles eller ett större separat aggregat.
- **Syntetiskt Difficulty-index:** senare Ultravasan-QA avråder från ett sammanvägt svårighetsbetyg. ÖST visar i stället de verifierbara dimensionerna separat: höjd, fart/spridning, pacing, platsrörelse och DNF.
- **Replay-/Kartduellmusik:** bedöms som presentation, inte analyskärna, och tillför autoplay-/tillgänglighetskostnad. Den generella replayfunktionaliteten är porterad.
- **Standalone kart-sida:** ÖST använder integrerad karta/replay och delningsbar URL-state i huvudprodukten; separat legacy-sida ger ingen ytterligare analysfunktion.
- **Cross-year head-to-head:** ÖST:s progressiva browsermodell laddar en RaceEdition åt gången. Historisk prestationsjämförelse görs via den lilla jämförbarhetsstyrda historikmodellen. En framtida cross-year duel ska först få ett uttryckligt on-demand-kontrakt.

## Datagränser som styr UI

- 2020–2021 är inställda och blir aldrig nollår.
- Historiskt saknat kön/ålder lämnas saknat.
- Trail 13/14 och Trail 5 får inte fabricerade splits/replay.
- Äldre Ultra kan ha splitanalys utan lokal rutt/replay.
- Duo analyseras som team; publiceringsordning är inte etappnummer.
- Historisk whole-course-prestation kräver explicit jämförbarhet.
- Route evidence är inte automatiskt en redistributerbar route asset.

## Bedömning

För den funktionalitet som ÖST:s verifierade data faktiskt stöder finns inga kvarvarande högprioriterade paritetsgap mot Gotaleden/Ultravasan. Kvarstående skillnader ovan är avsiktliga evidens-, arkitektur- eller tillgänglighetsbeslut och ska inte fyllas med heuristik.
