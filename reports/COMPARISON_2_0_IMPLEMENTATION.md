# ÖST Comparison 2.0 — implementation och capability-mappning

## Avgränsning

ÖST behåller sin befintliga Head-to-head-analys och sin separata Kartduell. Migreringen kopplar den verifierade tvåresultatsreplayen till Head-to-head och gör dess tillstånd delbart. Ingen source data, fryst total, provenance, CourseVersion- eller Engine 1.0-regel ändras.

## Implementationsplan

1. Låt adaptern härleda Comparison 2.0-förmågor från vald RaceEdition, två valda källresultat och deras faktiska observationer.
2. Behåll A/B-beräkningarna och analysordningen; rätta endast kontraktsdetaljer för placeringsaxel, stabil fältmedian och capability-styrd utelämning.
3. Återanvänd `map-engine.js` för en inbäddad tvåresultatsreplay med gemensam klocka, två markörer, synkad höjdprofil, seek, kamera och ljud.
4. Synka checkpoint- och segmentval med replayen och spara explicit jämförelsetid/segment i delnings-URL. URL uppdateras vid avslutad användarinteraktion, aldrig i varje animationsbild.
5. Nollställ jämförelsens beroende state vid byte av upplaga eller valda resultat. Behåll Kartduell för 2–5 deltagare/lag.
6. Bevisa rik Ultra 60, gles Ultra 60, Duo/team, kort splitfri bana och ruttlös upplaga i unit- och browser-QA.

## Capability-mappning

| Capability | ÖST-regel |
|---|---|
| `finish_comparison` | Visas för två resultat i samma RaceEdition när båda har publicerad fullföljd sluttid; annars används sista gemensamma verkliga passage/status. |
| `checkpoint_gap` | Kräver samma upplaga och exakta publicerade passager för båda. `gap = B elapsed - A elapsed`; positivt betyder A före. |
| `placement_journey` | Endast publicerad totalplacering. Saknad placering bryter serien och plats 1 ligger högst. |
| `segment_comparison` | Endast verkliga angränsande analysgränser där båda har observationer. Inga syntetiska kortbanesegment. |
| `edition_field_normalization` | Samma upplagas kompletta `FINISHED`-kohort, minst fem säkra segmentobservationer. 0 % är fältmedian; positivt är snabbare. |
| `shared_course_context` | Kräver upplagans egen lokala route asset med matchande CourseVersion. Ingen annan upplagas geometri lånas. |
| `animated_two_result_comparison` | Kräver två replay-klara resultat med minst två verifierade ankare på upplagans egen rutt. |
| `elevation_seek` | Visas endast tillsammans med inbäddad replay och källstödd lokal höjdprofil. |
| `shareable_comparison_state` | Alltid för giltigt tvåresultatsval; race och A/B återställs. Tid/segment följer med när replay/segment stöds. |
| `cross_edition_comparison` | `false`. Val och analys är fortsatt RaceEdition-lokala. |
| `sparse_comparison_fallback` | START → verklig kontroll → MÅL, eller endast verkliga tillgängliga steg. Ingen passage eller placering fabriceras. |
| `team_entity` | Duo jämför publicerade lagresultat. Medlemsordning blir aldrig etappnummer. |
| `audio` | Samma ÖST-ljud och persistens som Kartduell, 30 % första standardvolym, start först efter Spela och full cleanup vid stängning. |

## Oberoende degradering

Analys och geometri gateas var för sig. En ruttlös upplaga kan fortfarande visa giltiga sluttids-, passage- och segmentmått. En splitfri kortbana kan visa giltig sluttidsjämförelse och delningslänk men får inga påhittade passage- eller segmentpaneler. En gles upplaga behåller trestegsberättelsen och kan ändå få replay om just den upplagans rutt och tidsankare stöder den.

## Slutlig QA

Den slutliga versionen passerade foundation- och prebuildvalidering,
source-model integrity med 0 fel, 25 Python-test, 43 frontendtest och hela
browserregressionen. Browserfallen omfattar rik, gles, Duo/team och ruttlös
jämförelse, delning/återställning i en ny page state, URL Back/Forward,
placeringsaxel, checkpoint-seek, replaylivscykel samt 1440/900/768/390 utan
dokumentoverflow. Frysta source-totaler är oförändrade: 34 upplagor, 9 871
resultat och 6 123 splitpassager.
