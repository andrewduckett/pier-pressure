## Context

The card from #181 builds its strip in a pure model, `card/src/strip.ts`:
`buildStrip(states, pier, now, timeZone)` returns the axis, the time labels
and four cloud rows of cells. The card, `card/src/pierpressure-card.ts`,
renders that model as a CSS grid with a label column and a track column. It
positions cells and time labels in percent of the axis. Each row is a
`display: contents` element carrying `data-row`, so its label and track are
grid items of the strip.

The card redraws only when Home Assistant sets `hass`. It reads `Date.now()`
during render, so the fallback axis already follows the browser's clock.

The sun and moon altitude sensors carry `forecast` lists of
`{datetime, value}` points in the same shape as the cloud sensors. Each value
is the altitude at the start of its hour (`docs/night-timeline.md`).

## Goals / Non-Goals

**Goals:**

- Add the Sun altitude row, the Moon up lane and the three lines to the same
  pure model, so every new rule is tested through the existing card harness.
- Draw lines that cross the rows and the lane at any card width, without
  measuring the DOM.
- Leave room for the later all-rows story to add rows between Sun altitude and
  Cloud cover without reworking the lines.

**Non-Goals:**

- The Moon altitude row, the other condition rows and the moon drawing.
- Interpolating the moment the moon rises or sets inside an hour. A bar runs
  in whole hours, as in the YAML strip.
- Keeping labels apart when the now line is close to dusk or dawn.

## Test Seams

- **Primary test seam:** the card harness, `card/test/harness.ts`: mount the
  real `pierpressure-card` with a fake `hass`, then read the strip from the
  shadow DOM. Vitest's fake timers pin the browser's clock and advance the
  card's minute timer.
- **Existing seams reused:** `card/test/harness.ts` (gains helpers for the sun
  and moon sensors, and readers for bars and lines), `card/test/strip.test.ts`
  and `card/test/register.test.ts` (the card's size), and
  `tests/test_night_card_doc.py` for the docs scenario.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`,
  `docs/night-card.md` and its test. No contract, schema, delivery or build
  change.

## Decisions

### DD1. One row table for the Sun altitude and cloud rows

The model's row table gains a unit and a shade rule per row. The Sun altitude
row has the key `sun_altitude`, the unit `°` and the twilight shade rule. Each
cloud row has the unit `%` and the existing 15% rule. `buildStrip` returns
`rows` as Sun altitude first, then the four cloud rows. Every row uses the
existing cell rules: an hour per point, cut off at the axis ends, a blank hour
for a null value, and an empty row for a missing or unavailable sensor. The
hover text becomes `<label>, the hour from <HH:MM>: <value><unit>`.

- Alternative: a separate function for the Sun altitude row. Rejected: it
  would copy the clipping and blank-hour rules, which the spec says are the
  same.
- The later all-rows story adds its rows to the same table.

### DD2. The twilight shade rule

`sunShade(v)` gives step 0 above 0°, step 1 above −6°, step 2 above −12°,
step 3 above −18°, and step 6 otherwise, in the same seven blues as the cloud
rows. This is the YAML strip's band, so −18° exactly counts as night.

### DD3. Moon up runs from a map of hours

The model reads the moon altitude forecast into a map from hour to value,
skipping points without a readable `datetime`. It walks the hours in time
order. An hour joins the current run when its value is a finite number above 0
and it starts exactly where the run ends. Any other hour ends the run. Each run
becomes a bar with:

- `start` and `end`: the run's own hours, used for the hover text;
- `from` and `to`: the run cut off at the axis ends, used for drawing.

A run wholly outside the axis gives no bar. Sorting the map's hours makes the
rule hold even if a forecast arrives out of order. A missing or unavailable
sensor, or a `forecast` that is not a list, gives no bars.

### DD4. The dark window is read once

`stripAxis` splits into `darkWindow(attribute)`, which returns
`{dusk, dawn}` or `undefined` under DD7 of #181's rules, and the axis built
from it. `buildStrip` returns the window as `night`, so the dusk and dawn
lines are drawn exactly when the axis came from the window.

### DD5. Lines as an overlay placed on the grid

The model returns `lines`: up to three of `{kind, at, text}`, where `kind` is
`dusk`, `dawn` or `now`. The now line is included only when
`axis.start <= now <= axis.end`.

The strip grid gains explicit rows, `grid-template-rows`, generated from the
model's counts: a marks row, the rows, the Moon up lane, and the time labels.
The `.strip` element is `position: relative`. The lines sit in one element,
`.lines`, that is `position: absolute` with `grid-column: 2` and a
`grid-row` from the Sun altitude row to the Moon up lane. An absolutely
positioned child of a grid takes its grid area as its containing block, and
takes no part in auto-placement, so the other items stay where they are.
Inside it, each line is placed with `left` in percent of the axis.

Each line is a transparent box 8 px wide, centred on its instant, with a
2 px stroke drawn down its middle: dashed `#898781` for dusk and dawn, solid
`#e66767` for now. The overlay has `pointer-events: none`, and each line box
has `pointer-events: auto`, so a line shows its `title` and the cells around
it keep theirs. Each line's `title` and `aria-label` read `Dusk, 20:30`,
`Dawn, 03:25` or `Now, 22:00`.

The labels `dusk`, `dawn` and `now` sit in the marks row, above the Sun
altitude row, placed and centred like the time labels, in the line's colour.

- Alternative: one line segment inside each track. Rejected: the 2 px gaps
  between rows break the stroke, and a test would count one line many times.
- Alternative: an absolute overlay over the whole strip, offset by the label
  column's width. Rejected: that width is `max-content`, known only after
  layout.

### DD6. The Moon up lane

The lane is a grid row like the cloud rows, but its element carries
`data-lane="moon_up"`, not `data-row`, so readers of the condition rows do not
count it. Each bar is a `.bar` with `left` and `width` in percent of its drawn
span, `border-radius: 4px` and the grey `#898781`, with no inset, since bars
never touch. A bar carries `data-start`, `data-end`, `data-from` and
`data-to`, and its `title` and `aria-label` read `Moon up from 16:00 to 18:00`.

### DD7. A minute timer owned by the card

`connectedCallback` starts `setInterval(() => this.requestUpdate(), 60_000)`
and `disconnectedCallback` clears it. Render already reads `Date.now()`, so
each tick moves the now line and, on the fallback axis, the axis itself. The
timer does not align to whole minutes: the line is at most a minute behind,
under a pixel on a typical card.

- Alternative: a `now` reactive property set by the timer. Rejected: render
  would also need a fresh `now` on every `hass` update, so there would be two
  sources of the time.

### DD8. Test surface

Lines carry `data-line` with their kind and `data-at` with their instant as
an ISO string. The marks row's labels carry the same `data-line`. Bars carry
the data attributes in DD6. Rows keep `data-row`, now including
`sun_altitude`.

### DD9. The card grows by one row

`getCardSize()` returns 6 instead of 5: the marks row, the Sun altitude row
and the Moon up lane add about 50 px, one card row.

No decision here is costly to reverse: each sits inside the card's own
source, behind the published entities.

## Risks / Trade-offs

- [The now label overlaps the dusk or dawn label when the times are close]
  → Accepted, as in the YAML strip. Hovering over each line still names it.
- [An 8 px line box hides the hover of the cells beneath it] → Only across
  8 px; the rest of each cell keeps its hover.
- [A Moon up bar can start or end up to an hour before the moon really rises
  or sets] → It follows the hourly altitudes, as the YAML strip does; the
  docs say each altitude is for the start of the hour.
- [The timer keeps running while the browser tab is hidden] → Browsers slow
  hidden-tab timers; one redraw a minute is cheap either way.
- [happy-dom does not lay out the grid, so tests cannot prove the lines span
  the rows] → The tests assert the overlay's grid placement in its style;
  `mise run dashboard-check` checks the drawing by eye.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card source; the
published entities are unchanged.
