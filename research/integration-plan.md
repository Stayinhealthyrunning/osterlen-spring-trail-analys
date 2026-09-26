# Integrationsplan – Loppanalys Engine 1.0

ÖST ska byggas mot det frysta semantiska kontraktet `loppanalys-engine-1.0`, inte som en kopia av Gotaleden eller Ultravasan.

## Referensansvar

**Gotaleden** är referens för eventportabilitet, deltagartyp (person/team), tävlingsformat, capability-driven UI, framtida editions och event-scopad state.

**Ultravasan** är referens för progressiv dataladdning, explicit route evidence, verifierad flerårsidentitet, course/history intelligence och senare analysmoduler.

ÖST återanvänder kontrakten och algoritmerna där de passar men behåller sin egen source/provenance-normalisering.

## ÖST-specifikt lager

ÖST äger:
- Sportstiming-import och fryst källarkiv,
- event-/år-/familjekatalog,
- banversioner och ruttproveniens,
- checkpointnormalisering,
- Duo/Bengtemölla-semantik,
- readiness/capability-evidens,
- ÖST-specifik presentation.

## Engine-lager

Engine 1.0 förväntar:
- event + race catalog,
- person/team och competition format explicit,
- records/splits/checkpoints,
- course versions och route bundles,
- capabilities per RaceEdition,
- evidensstyrd historik/jämförbarhet.

Gemensamma funktioner kan omfatta sök, profil, percentiler, pacing/segment, head-to-head, kartmotor/replay, höjdprofil, historik, favoriter och delningsbara länkar — men endast när aktuell RaceEdition har capability för funktionen.

## Integrationsgrind

Ingen frontendfunktion får härleda stöd från namn, distans eller familj. Feature availability ska komma från data/readiness. Ingen source-observation får skapas för att fylla en UI-komponent.

ÖST:s flerårsmodell är förstaklassig i kontraktet; den läggs inte ovanpå en antagen enårsmodell.
