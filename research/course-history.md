# Banhistorik – arbetsunderlag

## Period

Analysen börjar 2018. Därmed lämnas den tidigare 47 km-ultran och äldre kortbanegenerationer utanför huvudmodellen.

## Ultra 60

Kända historiska banskällor visar tydliga skillnader i rapporterad geometri/längd mellan år. `course_version` lämnas därför avsiktligt tom tills GPX-filerna jämförts. 2024 samt 2025/2026 har arrangörslänkade GPX-filer som kan hämtas direkt med projektets fetch-script.

Den nuvarande arrangörens roadbook anger dessutom att delen Vik–Stenshuvud har ändrats efter stormen Babet och att markeringen på tävlingsdagen alltid gäller framför GPX.

## Duo

Duo infördes 2019 och använder samma fulla bana som Ultra 60. Bengtemölla är växlingsområde. Distansfördelningen ska härledas från faktisk växlingspunkt på respektive års geometri, inte antas vara exakt 30+30 km.

## Trail 21/22

Trace de Trail-källorna pekar på en mycket stabil rapporterad längd omkring 21,8 km under den moderna perioden. Detta är lovande för flerårsjämförelse, men identisk geometri måste fortfarande bevisas med GPX.

## Trail 13/14 och Trail 5

Båda kortbanorna har nu lokalt användbar, provenance-märkt referensgeometri från arrangörens egna kartbilder.

Trail 5-kartan georefereras med SWEREF 99 TM. Vid visuell kontroll av originalbilden upptäcktes att övre högra östkoordinaten är **E 437465**; den tidigare projekttranskriptionen **E 437965** var 500 m fel. Med korrigerad kalibrering ger den direkt extraherade/smidigt förenklade arrangörslinjen **5.003 km**, i praktiken identiskt med den tidigare manuella kontrollen 5.002 km.

Trail 13/14 rekonstrueras nu från sin **egen** arrangörsraster, inte som "hela Trail 5 + östslinga". Den legacy-märkta 13 km-kartan ger **13.084 km** efter borttagning av pixeltrappning. Hallamölla ligger 9.6 m från linjen och passeras med 4.634 km kvar, vilket oberoende stämmer väl med 2023 års deltagarmetadata.

Det som fortfarande saknas är inte familjegeometri utan **årsspecifik identitet**: ett komplett verifierat GPX-arkiv för samtliga analysår finns inte, och den nuvarande 14 km-sidan bäddar fortfarande in en legacy-karta märkt 13 km. Referensrutterna får därför användas för kart-/terrängvisning med tydlig provenance men får inte fabricera course-version-identitet mellan år.
