# Österlen Spring Trail Analys

Interaktiv analys av Österlen Spring Trail – resultat, banor, pacing och loppets utveckling från 2018 och framåt.

## Omfattning

Projektets analysperiod börjar 2018, då den moderna tävlingsstrukturen etablerades. Genomförda upplagor i scope är 2018, 2019, 2022, 2023, 2024, 2025 och 2026. Åren 2020 och 2021 registreras som inställda och får aldrig tolkas som saknad resultatdata.

Banfamiljer:

- `ultra60` – individuella ultraloppet.
- `duo60` – tvåmannalag på samma fulla geometri som `ultra60`.
- `trail22` – historiskt marknadsförd som 21 km, senare 22 km.
- `trail14` – historiskt marknadsförd som 13 km, senare 14 km.
- `trail5` – 5 km.

## Dataprinciper

Sportstiming är källa för officiella resultat från 2018 och framåt. Rådata ska bevaras oförändrad när importen byggs.

Bangeometri versionshanteras separat från tävlingsnamn. Två år betraktas inte som samma banversion förrän GPX-geometrin har jämförts. Marknadsförd distans används därför inte som bevis för identisk bana.

Saknade mellantider, placeringar, checkpointpassager eller lagrelationer får aldrig interpoleras och presenteras som officiella observationer.

Duo har ingen separat ban-GPX: respektive års Ultra 60-geometri är master och Bengtemölla behandlas som växlingspunkt när den officiella placeringen för året har verifierats.

## Förberedda källor

- `data/source/sportstiming/events.json` – officiella Sportstiming-event 2018–2026.
- `config/course-source-manifest.json` – inventering av kända officiella/externa banskällor och deras verifieringsstatus.
- `data/source/maps/manifest.json` – arrangörens nedladdningsbara kartunderlag.
- `research/` – metod- och datanoteringar.
- `tools/fetch_official_assets.py` – hämtar endast uttryckligen tillåtna arrangörsfiler från `osterlentrail.se`, validerar GPX/PDF och skapar SHA-256-kontrollsummor.

## Viktigt om GPX

Trace de Trail används i nuläget som historisk referens och för faktametadata. Tredjeparts-GPX ska inte kopieras in i det publika repot automatiskt innan återanvändningsrätten är klarlagd.

GPX som ÖST själva länkar för direkt nedladdning kan hämtas med:

```bash
python tools/fetch_official_assets.py
```

## Nästa tekniska steg

1. Kör hämtaren i en miljö med internetåtkomst.
2. Kartlägg Sportstimings publika nätverksanrop/endpoints för resultat, klasser och mellantider.
3. Hämta historiska GPX med klar proveniens.
4. Kör geometrisk jämförelse och tilldela först därefter `course_version`.
5. Integrera den generiska analyskärnan från Gotaleden när dess refaktorering är färdig.
