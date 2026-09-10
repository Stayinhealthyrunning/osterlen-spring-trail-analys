# Sportstiming – datainventering

## Officiella event

Event-ID och resultatsidor finns i `data/source/sportstiming/events.json` och är verifierade mot ÖST:s officiella resultatarkiv.

## Känd åtkomstsituation

Direkta automatiserade HTML-anrop mot resultatsidorna möter för närvarande en JavaScript-baserad human-verification. Detta säger inte att underliggande tävlingsdata saknas, bara att vanlig server-side HTML-skrapning är olämplig.

## Nästa undersökning

För ett fullvärdigt Gotaleden-liknande verktyg behöver vi kartlägga för varje år:

- eventets race/klass-ID:n
- deltagar/resultatfält
- status (FIN/DNF/DNS etc.)
- brutto- och nettotid
- kön/klass/ålder/födelseår där publikt
- klubb/lag
- Duo-lag och lagmedlemmar
- faktiska mellantids-/checkpointpassager
- splitplaceringar om de finns
- tracking/replay-data om den exponeras publikt

Importören ska först byggas när endpoints eller officiell export är stabilt identifierade.
