# Banhistorik – verifierat arbetsunderlag

## Period

Analysen börjar 2018. Den tidigare 47 km-ultran och äldre kortbanegenerationer ligger utanför huvudmodellen. Marknadsförd distans och faktisk bangeometri behandlas separat.

Maskinläsbar source of truth är `config/course-versions.json`.

## Ultra 60

- **2018 – `ultra60-2018`**: egen, tydligt längre historisk geometri; beräknad publik kartgeometri ca 62,055 km.
- **2019 – `ultra60-2019`**: separat fingerprint men mycket starkt geometriskt kompatibel med 2022–2023.
- **2022–2023 – `ultra60-2022-2023`**: exakt samma publika kartgeometri.
- **2024 – `ultra60-2024`**: materiellt förändrad bana; arrangörs-GPX är lokalt arkiverad.
- **2025–2026 – `ultra60-2025-2026`**: samma arrangörsruttkälla; arrangörs-GPX är lokalt arkiverad.

Arrangörens roadbook anger att tävlingsdagens markering alltid gäller framför GPX. Det ska behållas som metodbegränsning även när lokal GPX finns.

## Duo

Duo infördes 2019 och använder samma fulla geometri/course_version som samma års Ultra 60. Bengtemölla är växlingsområde. Distansfördelningen får inte hårdkodas som 30+30 km utan ska härledas från faktisk växlingspunkt på respektive års geometri.

## Trail 21/22

- **2018**: ännu inte formellt tilldelad. Kandidat Trace 7897 är geometriskt starkt kompatibel med 2019 men har `dateCompet=16/04/2016`; årsspecifik proveniens saknas.
- **2019 – `trail22-2019`**: verifierad publik geometri.
- **2022–2024 – `trail22-2022-2024`**: exakt samma publika kartgeometri.
- **2025–2026 – `trail22-2025-2026`**: exakt samma publika kartgeometri; mycket nära 2024 men separat fingerprint/version.

Äldre Trail 21/22-geometri kan stödja jämförbarhet men är inte automatiskt en redistributerbar lokal route asset.

## Trail 13/14

Den tidigare 14,249 km rekonstruktionen från arrangörens rasterkarta är bevarad som forskningsartefakt men **superseded** efter visuell kontroll i riktig kartmiljö, där systematiska korridorförskjutningar blev tydliga.

Nuvarande arbetsreferens är **13,472 km** och lagras som recept, inte som officiell GPX:

1. använd verifierad Trail 21/22-geometri 2022–2024 från start,
2. följ den till första Hallamölla-passagen,
3. ta bort den östra **8,269 km** slingan mellan två Hallamölla-passager som ligger endast **0,18 m** från varandra,
4. fortsätt på samma Trail 21/22-geometri till mål.

Härledd distans:
- start → Hallamölla: **8,687 km**
- Hallamölla → mål: **4,784 km**
- totalt: **13,472 km**

Det stämmer väl med den verifierade 2023-deltagaraktiviteten: klockdistans 13,67 km och anteckning om cirka 4,5 km kvar vid Hallamölla. Detta är ändå en **provisorisk arbetsmodell** tills autentisk deltagar-/arrangörs-GPX har säkrats.

## Trail 5

2026 har en rekonstruerad referens:
- OSM-snappad rutt: **5,481 km**
- oberoende full arrangörsraster-skeleton: **5,545 km**
- differens: ca 64 m.

Ruttens status ska alltid framgå som rekonstruerad, inte arrangörs-GPX. Historisk exakt år-till-år-identitet är fortfarande öppen.

## Publiceringsregel

En verifierad course_version och en redistributerbar/local route asset är två olika saker. Kart-/replayfunktioner får endast använda en lokal route asset när provenance/policy uttryckligen tillåter det. Tredjepartsgeometri som använts för diagnostik eller jämförbarhet ska inte automatiskt återpubliceras.
