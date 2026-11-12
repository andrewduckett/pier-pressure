## Why

Since #97, the verdict judges only the rest of the night once dusk has passed,
but the target list still judges the whole night. At 22:00 it still lists
targets that set at 21:00, and it scores the rest as if their whole window were
still ahead. A mid-session refresh then answers "what should I point at?" with
targets you can no longer image.

## What Changes

- Once the night has started, target ranking gates and scores each target on
  its **remaining window**: the longest stretch above the horizon mask within
  the **scored window**, from the scoring instant to `dark_window.end` (D2).
  This can be a different stretch from the published `window`.
- All four geometry terms use the remaining window: altitude, moon separation,
  window length as a share of the scored window, and transit (D1). Brightness
  and field-of-view fit do not change.
- A target with less than the minimum observable time (60 minutes) left is not
  listed, so the list is empty in the last hour of the night (D4).
- Each target gains an additive `remaining_window` {start, end}. `window`,
  `max_altitude`, `transit_time` and `moon_separation` keep their whole-night
  meaning (D3).
- Before dusk the list is unchanged, apart from the new field (D7).
- The night's catalog scan stays cached per night. A recompute later in the
  same night does not rescan the catalog, and its result equals a fresh
  computation at that instant (D5).
- The "Top pick" framing sentence follows the new top pick (D8).

No change is **BREAKING**: the delivery surface and every existing field keep
their meaning.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `target-ranking`: the minimum-duration gate, the geometry score terms and the
  determinism rule work over the remaining window once the night has started.
  A new requirement adds the `remaining_window` field.
- `night-verdict`: the requirement listing each target's fields adds
  `remaining_window`.

## Impact

- **Code:** `pierpressure/core/ranking.py` (`rank_targets`, `_rank`, the
  cache), `pierpressure/core/model.py` (`Target`),
  `pierpressure/core/producer.py` (passes the scored window to ranking).
- **Tests:** the ranking tests, and the golden documents under
  `tests/fixtures/golden/expected/`, which gain `remaining_window` and change
  in the mid-session fixture.
- **Docs:** `docs/target-ranking.md` and the README's description of target
  fields.
- **Delivery:** none. The top-target and rank sensors already publish every
  target field as attributes, so the new field reaches Home Assistant as it is.
  Drawing it on the card is #277.
- **Explainer:** `pierpressure/explain/prompt.py` renders every target field,
  so the optional narrative's prompt gains `remaining_window` too.
- **Glossary:** scored window, scoring instant and remaining window are now in
  `openspec/glossary.md` (D6).
