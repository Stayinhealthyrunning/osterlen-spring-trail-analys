# Withheld-truth benchmark

Use a race with a trusted organizer GPX as ground truth.

## Procedure

1. Freeze the trusted GPX and its checksum as the hidden truth artifact.
2. Remove that GPX and any direct derivatives from the evidence available to the reconstruction pipeline.
3. Supply only the weaker evidence classes that would exist for a difficult race: organizer raster, descriptions, participant evidence, path network, local trail maps and controls.
4. Reconstruct the route without inspecting the truth geometry.
5. Freeze the reconstructed artifact.
6. Compare reconstruction against truth.

## Metrics

Report at minimum:

- reconstructed length versus truth length;
- symmetric median nearest-line distance;
- symmetric 95th-percentile nearest-line distance;
- maximum material deviation after excluding isolated GPS noise;
- percentage of reconstructed route within 10 m, 25 m and 50 m of truth;
- mandatory-control pass/fail and order;
- start/finish displacement;
- unresolved-alternative count;
- false-confidence rate: segments marked high/canonical that materially disagree with truth.

## Why symmetric distance

Measuring only reconstructed points to the truth can hide a missing loop or shortcut. Measure both reconstruction -> truth and truth -> reconstruction.

## Acceptance thresholds

Do not hard-code universal thresholds before benchmark data exists. Forest trail GPS, road races and mountain ultras have different achievable precision. Establish thresholds empirically by race type after multiple withheld-truth cases.

## First benchmark candidate

Prefer an existing Loppanalys race with a trusted organizer/reference GPX and good map evidence. Gotaleden is a natural candidate because its analysis implementation is already treated as a stable reference project. The benchmark must use a frozen copy/checksum so later route edits cannot move the goalposts.
