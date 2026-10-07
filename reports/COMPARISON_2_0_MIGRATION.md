# ÖST → Loppanalys Comparison 2.0 migration plan

## Goal

Converge Österlen Spring Trail's comparison UX on the shared Comparison 2.0
contract while preserving the two things ÖST contributes back to the standard:

1. **first-class sparse comparison**, and
2. **person/team capability semantics** for individual and Duo data.

Canonical contract:

- `Stayinhealthyrunning/ultravasan-analys/config/comparison-contract-v2.json`
- explanatory reference: `reports/COMPARISON_2_0.md`.

## Current strengths to preserve

ÖST is already close to the analytical reference. It has:

- exact two-result Head-to-head;
- final gap, passages led, lead changes, nearest/largest gap and most-time-won KPIs;
- signed checkpoint-gap journey;
- official placement journey;
- clickable segment duel;
- field-relative pacing;
- route/elevation context;
- separate Kartduell;
- a purpose-built sparse mode for one-intermediate-checkpoint cases;
- support for both person and team/Duo semantics.

The migration must build on this rather than replace it.

## Primary gap: continuous two-result interaction

The main missing piece is the interactive layer now present in Ultravasan and
Sätila. Where the selected edition exposes replay + local route capability,
Direct Comparison should include:

- two reconstructed participant/team positions;
- one shared race clock;
- play/pause/reset;
- time scrubbing;
- 30 s / 1 min / 2 min / 3 min playback choices;
- 2 min default;
- whole-course / follow-both / follow-leader camera modes where supported;
- synchronized elevation markers;
- elevation-profile seeking;
- checkpoint and segment clicks that seek/highlight the same analytical state;
- race-family soundtrack with 30% neutral default volume.

Continuous motion remains reconstruction between real timing anchors.

## Sparse mode is part of the contract

Do **not** force the full chart stack onto an edition with too little timing.

The existing START → observed checkpoint → FINISH story is the intended
Comparison 2.0 fallback. It should remain explicit and gain the same shared
interaction language where evidence allows it.

Examples:

- finish/status comparison may still be available;
- one real intermediate checkpoint can still show observed gap and place;
- map/replay may be available independently from analytical segment density;
- no additional analytical checkpoints may be invented.

Short-course editions with no intermediate split table must stay split-free.

## Team/Duo rules

`participant.entity=team` must be preserved where applicable.

- Compare the published team result, not invented member legs.
- `source_sequence` is source publication order, not leg number.
- Member data may be displayed only according to existing source semantics.
- Field reference for team comparison must remain stable and explicitly
  described by the adapter.

## Alignment work

### Common section order and copy

Align the visible comparison flow to:

1. participants;
2. KPI strip or sparse story;
3. gap journey where supported;
4. placement journey where supported;
5. segment duel;
6. field-relative performance;
7. interactive course/elevation;
8. method/data quality.

Use the shared A/B sign convention: positive checkpoint gap means A is ahead.

### Share state

Make Direct Comparison restorable from a URL with the two selected result IDs
and supported state. Preserve the existing Kartduell URL behavior.

### Audio/replay defaults

Use the shared replay defaults where audio exists:

- 120 s default;
- 30/60/120/180 s choices;
- 30% neutral volume;
- persisted on/off and volume;
- reduced-motion compatible.

## Explicit non-goals

- Do not add cross-edition Direct Comparison yet.
- Do not create cross-year person identity from names.
- Do not reconstruct missing Sportstiming split observations.
- Do not convert short races into pseudo-split races.
- Do not infer Duo leg assignment.
- Do not replace the curated/frozen source architecture.

## Suggested implementation order

1. Add local comparison compatibility adapter/view-model.
2. Align A/B semantics and common copy/order.
3. Reuse existing full and sparse analytical branches unchanged where correct.
4. Embed two-result shared-clock replay into full comparison.
5. Add compatible interaction to sparse mode where route evidence allows.
6. Add audio/default controls and share state.
7. Extend browser QA with one rich edition, one sparse edition, one team/Duo
   case, and one route-unavailable case.

## Acceptance examples

A rich Ultra 60 edition should expose the full Comparison 2.0 analytical and
interactive stack. A race with one intermediate checkpoint should remain the
clear three-step sparse story. A short race without public splits must not gain
synthetic segment charts simply to match another Loppanalys event.
