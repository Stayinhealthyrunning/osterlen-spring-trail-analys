# Dataproveniens och källpolicy

## Prioritetsordning

1. Österlen Spring Trails/ADP sport events officiella webbplats.
2. Sportstiming för start-, deltagar-, resultat- och tidtagningsdata.
3. Arrangörsskapade banreferenser på Trace de Trail.
4. ITRA/UTMB och andra sekundärkällor endast som kontroll eller kompletterande metadata.

## GPX

En `.gpx`-fil i repot ska alltid innehålla den verkliga källfilen. Placeholder-filer med `.gpx`-ändelse är förbjudna.

Arrangörsfiler som uttryckligen erbjuds för nedladdning från `osterlentrail.se` får hämtas av `tools/fetch_official_assets.py`. Historiska Trace de Trail-spår lagras tills vidare som URL + metadata i manifestet. Själva tredjepartsgeometrin ska inte publiceras i repot förrän rättigheterna för återanvändning/redistribution har kontrollerats.

## Banjämförelser

Ingen flerårsjämförelse av segment får anta att samma marknadsförda distans betyder samma bana. GPX ska jämföras geografiskt. När jämförelsen är klar kan en explicit `course_version` tilldelas.

## Tidtagning

Sportstiming-sidorna använder för närvarande JavaScript/human-verification för automatiserade anrop. Ett framtida importverktyg ska därför baseras på dokumenterade publika requests/endpoints eller officiell export, inte på skör HTML-skrapning.
