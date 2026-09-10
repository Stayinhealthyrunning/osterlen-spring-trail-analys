# Remaining open questions after data freeze

This file intentionally contains only issues that cannot be closed from the current verified source material. It is not a general backlog.

## 1. Generic Gotaleden engine integration

**Status:** waiting on external project state.  
**Blocker:** the generalized `Stayinhealthyrunning/gotaleden-splits` engine/refactor should stabilize before ÖST imports that core.  
**Next action:** build an adapter from `data/derived/ost-analysis-2018-2026.sqlite.gz` to the finalized generic engine contract. Do not recrawl Sportstiming.

## 2. Historical local route assets

**Status:** source comparability is stronger than frontend asset availability.  
**Known:** course-version evidence exists for historical Ultra and most Trail 21/22 years.  
**Missing:** locally usable/redistribution-appropriate route assets for several historical versions.  
**Effect:** split analysis is possible for historical Ultra/Duo, but route-dependent replay/map remains disabled unless a local route asset exists.

## 3. Trail 13/14 and Trail 5 historical course versions

**Status:** unresolved.  
**Blocker:** no complete verified year-by-year route geometry archive has been secured.  
**Rule:** do not assign course versions from marketing distance/name alone.

## 4. Trail 21/22 in 2018

**Status:** intentionally unassigned.  
**Known:** candidate geometry is strongly compatible with the 2019 route.  
**Blocker:** candidate Trace metadata is dated 2016, so year-specific provenance is not strong enough for formal 2018 assignment.

## 5. Duo leg attribution

**Status:** member rows imported; leg numbers unresolved.  
**Known:** 599 published member rows are retained and `source_sequence` is preserved.  
**Blocker:** aggregate timing evidence does not validate that row 1/2 always means leg 1/2.  
**Rule:** keep `leg_no = NULL` until stronger source/organizer evidence exists.

## 6. Historical gender / age gaps

**Status:** source limitation.  
**Known:** 2022 has explicit age/gender categories; 2024–2026 have nearly complete exact age/sex.  
**Missing:** reliable published sex/age fields for individual results in 2018, 2019 and 2023 in the frozen public structures.  
**Rule:** never infer these fields from names.

## 7. Cross-year person identity / repeat runners

**Status:** not implemented by design.  
**Blocker:** names alone are not a guaranteed stable identifier.  
**Required method:** separate derived linkage table with normalized evidence, confidence, ambiguity handling and an explicit distinction from source-local participant identity.

## 8. Physical interpretation of Bengtemölla 2022–2023

**Status:** timing observations are known; physical interpretation is not.  
**Known:** `32 km` and `Bengtemölla` are separate published readings with a large/variable elapsed gap.  
**Hypothesis:** approach/prewarning followed by a later station-related reading is plausible.  
**Rule:** expose the gap only as a service-window/between-observation candidate until timing-mat placement or organizer documentation verifies the physical meaning.

## Explicitly not open anymore

The following are completed and must not be reintroduced as backlog items:

- full Sportstiming result import for 2018–2026;
- frozen source archive and checksums;
- archive data-quality audit;
- explicit DNF resolution where source evidence exists;
- curated engine database;
- Ultra split normalization;
- Duo team split parsing;
- Duo member-row parsing;
- safe recovery of start number, club/country and source-backed 2022 age/gender category;
- course-version model for Ultra and Trail 21/22 except the documented unresolved years;
- engine-readiness matrix.
