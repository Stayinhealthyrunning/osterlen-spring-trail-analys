# Deep route / GPS source sweep — 2026-09-26

## Scope

This sweep extends the existing organizer + Trace de Trail research with public participant activities, public route repositories, organizer map images and a harmonized elevation-source policy. No source is promoted to a local GPX asset unless actual GPX bytes have been obtained and validated.

## Material new findings

### Trail 13/14

The current organizer 14 km Race-PM still embeds a direct organizer-hosted route/elevation image:

- https://www.osterlentrail.se/uploads/4/1/8/7/41870619/13km-bana-h-jdkurvan-3_orig.jpg
- image label: **ÖST 13km bana**
- current Race-PM describes approximately 14 km, one lap, midpoint Hallamölla, mainly Skåneleden/Backaleden.

This closes the earlier statement that trail14 had no verified geometry evidence at all. It does **not** close the GPX gap: the image is not georeferenced and its legacy 13 km label means it cannot prove exact year-to-year identity.

### Trail 5

The current organizer Naturloppet page embeds a direct organizer-hosted course map:

- https://www.osterlentrail.se/uploads/4/1/8/7/41870619/st-5km-bana_orig.jpg
- image label: **ÖST 5km bana**
- Race-PM says one approximately 5 km lap in Christinehofs Ekopark, with gravel/forest roads and about 2 km narrow trail.

This provides verified organizer route-shape evidence for the 5 km family, but still not replay-grade GPX geometry or year-by-year version proof.

### Trail 21/22 — 2018 race-day evidence

A public Jogg activity from Jörgen Forsbacka is explicitly titled **Österlen Spring Trail 2018**, dated race day 2018-04-14, and records **22.03 km** with **319 m watch ascent**. The text identifies the 21 km race.

Reference:
https://www.jogg.se/Traning/Pass.aspx?id=15416220

This is independent race-day distance evidence supporting that the 2018 short course was around 22 km. It strengthens, but does not by itself solve, the provenance problem of Trace 7897 because no anonymously exportable coordinate series has been acquired.

### Duo 2019 — actual leg length evidence

A public Jogg/Movescount activity from Jörgen Forsbacka records **26.29 km** for Duo leg 2 on 2019-04-13. The participant text says the teammate logged nearly **33 km** on leg 1 and gives team finish time 6:19:46.

Reference:
https://www.jogg.se/Traning/Pass.aspx?id=17797161

This is useful real-world evidence that the relay must not be modelled as literal 30 + 30 km. The displayed watch ascent (1944 m) is clearly unsuitable as course D+ and is retained only as source metadata.

### Additional participant activity leads

- 2025 Duo: https://www.strava.com/activities/14154858457 — public landing page exposes **Österlen Spring Trail Duo 2025** for Jörgen Forsbacka; map/coordinates require login.
- 2026 Trail 22 lead: https://www.strava.com/activities/18157491795 — public landing page exposes **Österlen Spring Trail 2026** for Jörgen Forsbacka; ITRA results cross-check him in the 22 km race at 2:09:54; map/coordinates require login.

These are retained as acquisition leads, not local assets.

## Public route repositories

Two plotaroute leads are worth preserving:

- 2023: https://www.plotaroute.com/route/2332025 — **Österlen Spring Trail 60K-2023-M1**, listed at 57.646 km / 777 m.
- 2025: https://www.plotaroute.com/route/2795139 — **Österlen Spring Trail 60 K 2025 Official**, listed at 59.662 km and raw +798/-688 m. The page offers GPX/KML/TCX/FIT export.

The 2025 title's word *Official* is user metadata and is not treated as organizer provenance. Neither plotaroute route is classified as an actual race-day recording unless separate evidence proves that.

Wikiloc also indexes a 2025 route explicitly labelled as being from Trace de Trail (59.62 km / +476 m). Because it is derivative, it adds little independent geometry evidence.

## Elevation policy

Raw elevation must remain separate from harmonized elevation. The archived organizer GPX inventory already shows why: the 2024 organizer file has only partial elevation points and produces no usable raw D+, while the 2025/2026 organizer GPX has complete elevations but raw +1058/-942 m; third-party published D+ values vary materially by method.

For cross-year analysis, the preferred standardized terrain source is **Lantmäteriet Markhöjdmodell Nedladdning**, the current nationwide ground DEM with 1 m grid and RH 2000 heights. It is free under the valuable-datasets terms and is suitable for sampling one canonical route geometry with one common algorithm.

Recommended processing chain:

1. choose the best-supported canonical geometry for a course version;
2. resample horizontally at a fixed interval;
3. sample one common ground DEM for every point;
4. apply one documented elevation-noise / ascent filter to every course;
5. store source elevation, barometric reference elevation and standardized DEM elevation as separate fields;
6. never compare raw watch D+ directly with DEM-derived D+.

The project owner's 2025 Suunto barometric recording remains useful for profile-shape validation and filter sensitivity, but not as the universal D+ source.

## Current acquisition limits

The deep public search found more **references** than downloadable raw participant GPX files. Strava exposes the relevant activity landing pages but requires login for the activity map. Jogg exposes rich activity metadata; coordinate/GPX export is not anonymously exposed. Trace de Trail export remains login-gated in the existing probe. plotaroute advertises direct GPX download in its UI, but the current execution environment cannot fetch those bytes directly.

Accordingly, no fake GPX files have been created. New references are catalogued in `config/route-evidence-sources.json`.

## What is materially improved

- trail14: from “no route geometry archive” to **verified organizer map-shape evidence**, GPX still missing.
- trail5: from “no route geometry archive” to **verified organizer map-shape evidence**, GPX still missing.
- trail22 2018: independent **race-day distance evidence** now supports the candidate geometry, but exact coordinate provenance remains unresolved.
- duo60 2019: independent **race-day leg-length evidence** confirms materially asymmetric legs.
- ultra60 2023/2025: additional downloadable-route leads catalogued for later coordinate acquisition.
- elevation: a concrete common-source strategy based on Lantmäteriet's 1 m ground DEM is now defined.

