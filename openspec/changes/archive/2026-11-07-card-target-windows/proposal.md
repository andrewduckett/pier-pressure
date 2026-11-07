## Why

The card's strip answers "is tonight worth it" but not "what do I point at".
The YAML strip it replaces draws each ranked target's observable window on the
same axis as the conditions, so a viewer who installs the card loses that view
(#132, Should).

## What Changes

- Under the Moon up lane, the strip gets one lane per ranked target, Target 1
  first, read from `sensor.pierpressure_<slug>_target_1` to `_target_10`
  (D3, D5).
- A rank gets a lane only when its sensor exists, is not `unavailable`, and
  holds a usable `window`. An empty rank, a missing sensor or a broken window
  leaves no lane, and the card never throws (D4).
- The lane is labelled `Target <n>`. Its violet bar runs from the window's
  start to its end and holds the target's name (D6, D7).
- A bar is cut off at an axis end, as a Moon up bar is (D8). Hovering over it
  shows the target's name and its window's own times (D9).
- The dusk, dawn and now lines cross the target lanes (D10).
- The card's size grows with the number of lanes it shows (D11).
- `docs/night-card.md` describes the target lanes (D14).

The lane shows only the name and the window. Nothing in the core, the verdict
document or the MQTT delivery changes, and the card picks no targets (D12).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: new requirements give the strip its target lanes, their
  sensors, bars, hover text and docs, and the card's size per lane. The dusk,
  dawn and now lines widen to cross the target lanes.

## Impact

- Changed: `card/src/strip.ts` (the target lanes), `card/src/pierpressure-card.ts`
  (drawing the lanes, the lines' reach and the card's size), `card/test/`
  (lane tests and harness helpers), `docs/night-card.md` and
  `tests/test_night_card_doc.py`.
- No new dependencies.
- No change to `mise.toml`, CI, the release or `scripts/dashboard_check.py`:
  the dashboard check already shows the locally built card beside the YAML
  strip, Target sensors included (D15).
