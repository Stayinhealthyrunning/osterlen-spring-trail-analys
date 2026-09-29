# ÖST Splits – visuell och funktionell QA

Datum: 2026-09-29
Branch: `improve/ost-ux-parity`
QA-underlag: Chromium-artefakter i `artifacts/` (lokala, ignorerade körningsfiler)

## Resultat

Slutversionen godkändes i 14 automatiserade browserflöden, inklusive den nya hero-sökningen, tangentbordsautocompleten, könstoggles och den direkta Kartduell-ingången. Alla tillgängliga scrollsektioner renderas samtidigt; deep links fokuserar rätt sektion och browser Back/Forward återställer ankarpositionen. Resultatdatabasen och Kartduell förblir separata arbetsvyer.

| Viewport | Resultat |
|---|---|
| 1536 × 1024 | Godkänd. Fullbreddshero och familjekort går över i tydlig analysnavigation, KPI:er och tvåkolumnskort. |
| 1366 × 768 | Godkänd. Hero, lopp-/årsval och analyskontroller ryms utan dokumentoverflow. |
| 900 × 900 | Godkänd. Analyskort och diagram behåller läsbar bredd. |
| 390 × 844 | Godkänd. Hero, kort, verktyg och dialoger fungerar i mobilbredd; tabeller och diagram använder egna scrollområden. |

Geometriassertionen fann högst 2 px dokumentoverflow i samtliga storlekar och analyserade huvudsektioner. Den mobila profil-/replay-dialogen och `prefers-reduced-motion` verifierades. Browserkörningen rapporterade noll console errors, noll page errors och noll oväntade nätverksfel.

## UX- och designkrav som verifierades

- Hero är en bred, låg Österlen-kustbild med vänstergradient. Sökning efter namn/startnummer visar tangentbordsnavigerbara förslag och öppnar källstödd profilmodal. Kartduell har en tidig, fungerande ingång.
- Fem familjekort använder fem separata WebP-miljöer. Trailbilderna visar skog/inland; inget motiv utger sig för att exakt avbilda ett namngivet landmärke. Den innehållssvaga route-journey-sektionen är borttagen.
- Översiktens könskort, sluttidshistogram, percentiler och segmenttabell kan fokusera/dölja källstödda könsserier. Legend, antal och percentilvärden redovisas. Gruppkort för klass, åldersklass och klubb/ort visar stapelöversikt först och full tabell på begäran.
- Fältflödet visar inte startankaret 100 %. Status använder DNF. Metodguiden finns i Metod; analyskort har korta tillgängliga infoförklaringar.
- Capability-gränser höll: äldre Ultra behåller splits utan lånad rutt, finish-only-lopp saknar segmentsektion, Duo visas som lag utan härledda etapper och saknad CourseVersion utelämnar bansektionen.
- Browserflöden täckte tile-failure fallback, race-/årsbyte, global sökning, profil/replay, direktjämförelse, kartduell, historik, metodik, målplan, deep links samt Back/Forward.

## Regression och performance

- Foundation: godkänd.
- Prebuild readiness: godkänd.
- Python: 25 tester godkända.
- JavaScript: 26 tester godkända.
- Chromium: 14 browserflöden godkända över samtliga fyra storlekar.
- Frontend budget: godkänd. HTML 1 559 B gzip, CSS 9 840 B gzip, JavaScript 33 921 B gzip. Kritisk kod/dataöverföring är 77 704 B gzip mot budgeten 524 288 B. Bootstrap + största valda lopp är 32 384 B gzip; full Engine-regressionstoken är 450 547 B gzip.
- Lokal, headless Chromium rapporterade första användbara vy efter cirka 477 ms. Det är en okonditionerad lokal observation, inte ett nätverks-SLA.
- Hero-WebP är 287 096 B. De fyra familje-WebP-bilderna är tillsammans 203 126 B (490 222 B visuella bilder totalt). Performance-budgetens kritiska kod/data-mått exkluderar bilder. Route, elevation och replay förblir lazy-loaded.

Datagenerationens SHA-256 var `b55f8774887ca80586e1e40e5f8dd7c02a0de83c165b02b6d8c9500eea9a3693`; totals var fortsatt 34 lopp, 9 871 resultat, 6 123 observerade splits, 300 Duo-lag och 599 medlemsrader. Source data, Engine 1.0-kontrakt, frysta totaler, provenance och capability-regler ändrades inte.

## Kvarstående begränsningar

Ingen flerårig personidentitet eller Duo-etappkoppling skapades. Finish-only-upplagor saknar segmentdata. Kurs- och replayvyer fortsätter att följa lokal CourseVersion och provenance; kartor eller splits från andra upplagor lånas inte.

**VISUAL QA READY FOR HUMAN REVIEW: YES**
