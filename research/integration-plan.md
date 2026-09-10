# Integrationsplan mot Gotaleden-kärnan

ÖST-projektet ska använda den generiska analyskärnan från Gotaleden när den pågående generaliseringen är färdig. Målet är inte en fristående hårdkodad kopia.

## ÖST-specifikt lager

ÖST ska själv äga:
- event- och årskonfiguration
- tävlingsfamiljer och banversioner
- Sportstiming-import
- GPX- och kartkällor
- checkpoints och Duo-växlingar
- flerårsregler och jämförbarhet
- ÖST-specifik design/text

## Gemensam analyskärna

Så långt möjligt återanvänds:
- resultatdatabas och sök
- deltagar-/lagprofiler
- diagram och percentiler
- pacing- och segmentmotor
- head-to-head
- måltidssimulator
- kartmotor, Runner Replay och Kartduell
- höjd- och banprofil
- metodhjälp
- favoriter och delningsbara länkar

## Integrationsvillkor

Överföringen bör ske först när Gotaleden kan startas från en event-konfiguration utan att kärnfunktioner förutsätter Gotaleden-specifika race keys, checkpointnamn, stafettklasser eller ett enda tävlingsår.

ÖST:s flerårsmodell ska läggas ovanpå kärnan i stället för att pressas in i Gotaledens premiärårsmodell.
