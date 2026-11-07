## Context

The card's strip model, `card/src/strip.ts`, turns Home Assistant's states into
a plain `Strip` object: the axis, the fifteen rows, the Moon up bars, the lines
and the time labels. `card/src/pierpressure-card.ts` draws that object as a CSS
grid. Grid row 1 holds the line labels, then come the fifteen rows, the Moon up
lane and the time labels. The lines' overlay spans from the first row to the
end of the Moon up lane, and both its end and the grid's row count are worked
out from `strip.rows.length`.

A Moon up bar is a `Bar`: its run's own `start` and `end`, the part on the axis
as `from` and `to`, and its hover `text`. The card draws it as a grey `.bar`.

Each Target sensor, `sensor.pierpressure_<slug>_target_<n>` for `n` from 1 to
10, has the target's display name as its state. Its attributes are
`available`, `rank` and the target's fields at the top level, with `window` as
an object of `start` and `end` (`pierpressure/delivery/mqtt.py`,
`rank_target_attributes`). An empty rank is `unavailable`, and Home Assistant
then normally drops its attributes. The core clamps every window to the dark
window (ADR-0003), so on a fresh state every bar lies inside the axis.

`getCardSize()` returns a fixed 10, sized for fifteen rows.

## Goals / Non-Goals

**Goals:**

- Build the target lanes in the strip model, beside the Moon up bars, so the
  rules for reading a window are unit-tested through the same harness.
- Reuse `Bar` and its drawing, so a target bar and a Moon up bar are cut off at
  the axis in one way.

**Non-Goals:**

- Showing a target's score, altitude, transit or catalog facts.
- A different number of ranks than the ten the delivery publishes.
- Changing the rows, the Moon up lane's rules or the axis.

## Test Seams

- **Primary test seam:** the card harness, `card/test/harness.ts`: mount the
  real `pierpressure-card` with a fake `hass`, then read the lanes, bars and
  lines from the shadow DOM.
- **Existing seams reused:**
  - `card/test/harness.ts` gains a `targetEntity(name, window)` builder, a
    `TARGET` id helper and a `targetLanes(card)` reader.
  - `card/test/targets.test.ts` is a new file for the lanes, their bars, hover,
    the lines' reach and the card's size with lanes. `strip.test.ts` is already
    over 1000 lines. Its grid tests, which mount no Target sensor, stay as they
    are.
  - `card/test/register.test.ts` keeps the size of 10 for a card with no
    state.
  - `tests/test_night_card_doc.py` takes the docs scenario.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`,
  `docs/night-card.md` and its test. No contract, schema, delivery or build
  change.

## Decisions

### DD1. The strip model gains `targets`, a list of lanes

`Strip` gains `targets: TargetLane[]`, where a `TargetLane` is
`{ rank, label, name, bar? }`. `label` is `Target <rank>`, `name` is the
sensor's state, and `bar` is a `Bar` or is absent when the window is wholly
off the axis. `buildStrip` fills it with a `targetLanes(states, pier, axis,
time)` function that walks ranks 1 to 10 in order and keeps a rank only when:

- the entity exists and its state is not `unavailable`;
- `asRecord(attributes.window)` has a `start` and an `end` that `readTime`
  reads, and `end > start`.

The bar's `start` and `end` are the window's own times. `from` and `to` are
those times held to the axis. Its `text` is `<name> from <HH:MM> to <HH:MM>`,
from the window's own times, through the same `clock` as every other hover.

A lane's existence does not depend on the axis, so the lane count is the same
whatever the browser's clock says.

- Alternative: a lane object with its own window fields and no `Bar`.
  Rejected: the card would need a second bar renderer and a second clipping
  rule.
- Alternative: dropping a lane whose window is off the axis. Rejected: the
  spec keeps the lane, and the count, and so the card's size, would then move
  with the clock.

### DD2. A target bar is the Moon up bar with a name and a colour

The card draws each lane as `.row[data-lane="target_<n>"]`, with its label in
the label column and its bar in the track. `renderBar` takes an optional
label: a target bar passes `name` and sets `data-target`. CSS for
`.bar[data-target]` gives it the violet `#6250d6` background, white text at
`0.75em` with a 16 px line height, 4 px padding at the left, and
`overflow: hidden; white-space: nowrap; text-overflow: ellipsis`, so a long
name ends in `…` inside a short bar. The hover's `title` always holds the full
name.

White on `#6250d6` has a contrast ratio of about 5.8 : 1, above the 4.5 : 1 that
WCAG asks for normal text.

- Alternative: the name in the label column and a plain bar. Rejected: names
  such as "North America Nebula" would widen the label column and squeeze
  every row; the YAML strip writes the name on the bar too.

### DD3. The grid and the lines count the target lanes

The grid row count becomes `rows + 3 + targets`, and the lines' overlay ends at
grid line `rows + 3 + targets`, the start of the time labels' row. So the
dusk, dawn and now lines reach the bottom of the last target lane, and with no
target lane the numbers are as today.

### DD4. The card's size counts the lanes it shows

The card works out the strip it would draw in one private method that returns
the `Strip`, or `undefined` when it draws none: no `hass`, a missing Verdict
sensor or an unavailable one. `render` and `getCardSize` both call it.
`getCardSize()` returns `10 + Math.ceil(targets.length / 3)`. A lane is 16 px
with a 2 px gap, so three lanes are about one 50 px size unit.

- Alternative: a fixed size of 14 for the ten possible lanes. Rejected: on a
  night with few targets the dashboard would reserve empty space.

## Risks / Trade-offs

- [Home Assistant's masonry view asks for the size when it lays out the cards,
  not on every state change, so the size can lag a night's new lane count.] →
  The size is only a hint for balancing columns. The card's real height always
  fits its lanes, and the next layout picks up the new count.
- [An unavailable Target sensor whose attributes Home Assistant kept would
  show a stale window.] → The card checks the state first, as it does for the
  timeline sensors, and draws no lane.
- [A very short window leaves no room for the name.] → The ellipsis cuts it
  short, and hovering shows the full name and times.

## Migration & Rollback

N/A. The card reads entities that already exist. Rolling back means
installing the previous card file.
