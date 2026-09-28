# ÖST Splits – visuell QA

Datum: 2026-09-28  
Underlag: automatiserade Chromium-skärmbilder i `artifacts/` (lokala QA-artefakter, ej deploy)

## Granskade storlekar

| Viewport | Resultat |
|---|---|
| 1536 × 1024 | Godkänd. Hero, fem familjekort, tvåkolumnsanalys och tabeller håller tydlig hierarki. |
| 1366 × 768 | Godkänd. Kontroller och analysnavigation är synliga och användbara. |
| 900 × 900 | Godkänd. Tvåkolumnslayouten behåller läsbar diagramyta. |
| 390 × 844 | Godkänd. Kort stackas, metodguide blir en kolumn och tabeller/diagram scrollar internt. |

Automatisk geometriassertion verifierade högst 2 px dokumentoverflow i samtliga storlekar och i varje huvudsektion.

## Granskade vyer

- Landningssida och analysöversikt: tydlig ÖST-identitet, korrekt färgpalett och riktiga 2025-data.
- Individprofil med Replay: karta ligger högt, neutral kartbakgrund är begriplig och kontrollfältet är läsbart.
- Duo-profil: laget är analysobjekt; publicerade medlemmar visas utan etappanspråk.
- Kartduell: två deltagare, rutt, tidsreglage och höjdprofil fungerar i fokuserad dialog.
- Tile-failure: trasiga tilebilder tas bort; polerad neutral ruttvy behålls.
- Trail 5: rekonstruerad bana märks uttryckligt och får ingen Replay.
- Empty states: split- och ruttbegränsningar förklaras i text.

## Konkreta fynd och rättningar

1. Browserns `fetch` tappade sin bindning när den skickades till loadern. Loadern använder nu en omslutande funktionsanropare och startvyn laddar korrekt.
2. Några UI-tecken hade felaktig teckenkodning efter den första filskrivningen. Filerna normaliserades till UTF-8 och svenska tecken verifierades i Chromium.
3. Replaytestet sökte utanför vinnarens verkliga sluttid. Testet använder nu ett giltigt värde inom resultatradens publicerade tid.
4. 2024 års GPX har delvis saknade höjdpunkter. Höjdprofilen bryter kurvan vid saknad observation i stället för att omvandla saknad höjd till noll.

Inga ytterligare visuella fel mot releasekraven hittades. Den långa mobilsidan beror på den kompletta klassöversikten; tabellen håller sig inom sin egen scrollarea och orsakar inte dokumentoverflow.

## Automatiserad browser-QA

11 produktflöden passerade: progressiv laddning, tangentbordsprofil, Ultra Replay, Duo, historisk Ultra utan lånad rutt, 2023 års dubbla observationer, finish-only-familjer, lopp-/årsbyte, global sökning, Direktjämförelse/Kartduell, tile-failure, historik, metodik, loppplan, responsivitet och reduced motion. Rapporten hade 0 console errors, 0 page errors och 0 oväntade nätverksfel.

VISUAL QA READY FOR HUMAN REVIEW: YES

