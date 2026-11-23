<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

When the user pans the night strip to a later night, the target lanes are
empty: only tonight's ranked targets exist, and tonight's list is a poor guide
to another night. Ranked one night at a time, London's nights of 2026-11-21 to
24, with the moon at 87% to 100%, gave a fourth night whose top ten shared no
target with tonight's. #318 already gives each later night a `later_nights`
entry and a Night sensor, so this story only adds fields and lanes.

## What Changes

- **Core:** each later night is ranked with the same ranking as tonight, over
  its whole dark window, on its own moon (D1, D5). A later night's moon
  illumination and phase are computed at the middle of its local solar day,
  its local solar midnight (D3). Rise, set and up-during-dark are found within
  its own dark window.
- **Verdict document (additive):** each `later_nights` entry gains `moon` and
  then `targets`, after `dark_window`, in the shapes of the top-level `moon`
  and `targets` (D2). On a later night with no astronomical darkness, `moon`
  keeps its illumination and phase with null `up_during_dark`, `rise` and
  `set`, and `targets` is empty (D4). Tonight's fields do not change.
- **Scan cache:** the per-night scan cache keeps every night of every
  configured pier, so a recompute never rescans a night it already scanned
  (D7). It also keeps each later night's ranked list, so a recompute does not
  rank a later night again on the same moon; the user chose this in plan
  review, because a pier with a tight horizon mask would otherwise spend about
  14 s a night on every recompute. The cold first verdict after a restart
  takes about 20 s per pier instead of about 5 s; the user accepted this (D6).
- **Home Assistant delivery:** no new entity, topic or state. The Night 2 to
  Night 4 sensors' attributes already carry the whole entry, so `moon` and
  `targets` appear there (D8). The Verdict attributes still leave out
  `later_nights`.
- **Card:** the strip has a target lane for each rank that has a target on any
  night. Each night's bar sits in its rank's lane and is named for that
  night's target, with the same hover and tap text as tonight's bars (D9 to
  D11). Lane labels stay `Target <n>`.
- **Docs:** the README's Night sensor rows and `later_nights` row, and the
  panning and target-lane sections of `docs/night-card.md`.

Out of scope: a verdict, score or confidence for later nights; rank sensors
for later nights; the narrative. Open story #277 also edits the target lanes;
neither blocks the other.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: a later night entry holds `dark_window`, `moon` and
  `targets`, no longer only its dark window; adds when a later night's moon is
  computed and what its moon and targets hold.
- `target-ranking`: adds that a later night is ranked like tonight, over its
  whole dark window on its own moon, that a recompute reuses the scan of
  every night it ranked before, and that it reuses a later night's ranked list.
- `ha-delivery`: a Night sensor's attributes carry the entry's `moon` and
  `targets` as well as its `dark_window`.
- `night-card`: lanes come from every night's targets, not only tonight's; a
  later night's targets draw bars in their ranks' lanes; a target bar's tap
  key names its night; panning shows later nights' target bars; the docs
  describe them.

## Impact

- **Core:** `pierpressure/core/sky.py` (later nights with their solar days),
  `pierpressure/core/ranking.py` (rank several nights, the cache that keeps
  every night of a pier), `pierpressure/core/producer.py` (fill each entry),
  `pierpressure/core/model.py` (`LaterNight` gains `moon` and `targets`).
- **Delivery:** `pierpressure/delivery/mqtt.py` needs no code change; its
  tests gain the new attribute keys.
- **Card:** `card/src/strip.ts` (`targetLanes`), `card/src/tap.ts` and the bar
  rendering in `card/src/pierpressure-card.ts`, with tests in `card/test/`.
- **Contract:** additive only. Two new keys in each `later_nights` entry; no
  existing topic, entity, unique id or field changes.
- **Performance:** about 5 s more per later night on a cold scan, and about
  four scans per pier held in memory.
- **Docs:** `README.md`, `docs/night-card.md`, and an ADR in `docs/decisions/`
  if the ADR step finds one is needed.
- **Dependencies:** none.
