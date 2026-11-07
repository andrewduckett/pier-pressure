## Context

The card's strip model, `card/src/strip.ts`, builds every row from one table,
`ROWS`. Each entry has a sensor key, a label, a unit and a shade rule.
`buildStrip` turns each entry's `forecast` into cells: one per point, filling
the hour that starts at its `datetime`, cut off at the axis ends. A null hour
has no cell, and a missing or unavailable sensor gives a row with no cells.
Each cell's hover text is `<label>, the hour from <HH:MM>: <value><unit>`.
The table holds Sun altitude and the four cloud rows today.

The card, `card/src/pierpressure-card.ts`, draws the model as a CSS grid. Its
row count, and the span of the dusk, dawn and now lines, already come from
`strip.rows.length`, so more rows need no change there. Each cell is a
`.cell` with its shade as `background-color` and `data-shade`.

All fifteen timeline sensors carry `forecast` lists of the same shape.
`docs/night-timeline.md` says every value is for the hour that starts at its
`datetime`, except `precipitation_probability`, which is for the hour that
ends there. Open-Meteo follows that rule. The card cannot tell which provider
filled a value, so it follows the documented rule.

## Goals / Non-Goals

**Goals:**

- Add the ten rows to the same table, so the cell, blank-hour and
  missing-sensor rules stay in one place.
- Keep every new rule testable through the existing card harness.

**Non-Goals:**

- Converting units. The `forecast` attribute is always km/h and °C.
- A row picker, a dew-risk mark, or scaling a row to the night's own range.
- Changing the Moon up lane or the lines.

## Test Seams

- **Primary test seam:** the card harness, `card/test/harness.ts`: mount the
  real `pierpressure-card` with a fake `hass`, then read rows and cells from
  the shadow DOM.
- **Existing seams reused:**
  - `card/test/harness.ts` gains a constant for each new sensor.
  - `card/test/rows.test.ts` is a new file in the same style as
    `strip.test.ts`, which is over 1000 lines. It holds the added rows' tests.
    Tests in `strip.test.ts` that depend on the row count change in place:
    the row order, the row above the Moon up lane, the lines' grid rows and
    the strip's `grid-template-rows`.
  - `card/test/register.test.ts` checks the card's size.
  - `tests/test_night_card_doc.py` takes the docs scenario.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`,
  `docs/night-card.md` and its test. No contract, schema, delivery or build
  change.

## Decisions

### DD1. The row table grows to fifteen entries

`ROWS` lists the fifteen rows in the spec's order. Each entry keeps `key`,
`label` and `unit`, and gains two optional fields:

- `hourBefore: true` for Rain chance. The model takes the cell's `hour` as
  `datetime − 1 h`, then applies the usual axis rules to that hour. Every
  other rule, and the hover text, reads `hour`, so the hover names the start
  of the hour the cell fills with no special case.
- `value(v)`, which writes the value for the hover text. By default it is
  `${v}${unit}`. Wind direction writes `${v}° from ${compass(v)}`.

The units are `°` for the two altitudes, `%` for the cloud rows, Humidity and
Rain chance, ` km/h` for the wind rows, ` °C` for Temperature and Dew point,
and `""` for Seeing and Transparency. The leading space follows the SI style
for km/h and °C; `%` and `°` keep the existing hover text unchanged.

- Alternative: a separate builder for Rain chance. Rejected: it would copy
  the clipping and blank-hour rules for a one-hour shift.

### DD2. A row draws a shade or an arrow

Each entry has either `shade(v)`, returning one of the seven blues, or
`arrow(v)`, returning a rotation in degrees. `Cell` carries `shade` or
`arrow`, never both. All shade rules go through one helper, `blue(step)`,
which clamps the step to 0 to 6, so an out-of-range value never indexes past
the palette:

| Rule | Rows | Step |
|---|---|---|
| `percentShade` | the four cloud rows, Humidity, Rain chance | `floor(v / 15)` |
| `sunShade` | Sun altitude | the existing twilight steps |
| `moonShade` | Moon altitude | 0 at 0° or below, else `1 + floor(v / 6)` |
| `windShade` | Wind gust, Wind speed | `floor(v / 7)` |
| `qualityShade` | Seeing, Transparency | `Math.round((1 − q) × 7)` |
| `temperatureShade` | Temperature, Dew point | `floor((v + 10) / 5)` |

`cloudShade` is renamed `percentShade`, since it now serves three kinds of
row. `Math.round` rounds a half up, as the spec says, and matches the YAML
strip's `quality` exactly.

`windArrow(v)` returns `((v + 180) % 360 + 360) % 360`. `compass(v)` takes
`((v % 360) + 360) % 360`, divides by 45, rounds, and indexes
`N, NE, E, SE, S, SW, W, NW` modulo 8. A value halfway between two points
rounds up to the next one clockwise.

### DD3. The arrow is an inline SVG

A Wind direction cell is a `.cell` with no background, carrying `data-arrow`
with its rotation and no `data-shade`. The card omits the attribute a cell
does not use by binding Lit's `nothing`, since `undefined` would leave an
empty attribute. Inside the cell is an `<svg>` element written in Lit's
`html` template; Lit's `svg` template is only for content inside an `<svg>`.
It has a `viewBox` of `0 0 12 12`, one arrow path pointing up, and
`transform="rotate(<deg> 6 6)"` on its group. CSS gives the SVG
`display: block; width: 100%; height: 100%`, so it fills the 16 px cell
with no inline baseline overflow. The default `preserveAspectRatio` keeps the
arrow centred and as large as the cell's shorter side allows. Its colour is
`var(--secondary-text-color)`, so it reads in light and dark themes.

- Alternative: the `↑` character rotated with CSS. Rejected: its size and
  baseline vary by font, and some platforms draw arrows as emoji.
- Alternative: rotating the SVG element with CSS. Rejected: the cell is not
  square, so the box would swing outside the row at 90°.

### DD4. The card grows to fit

`getCardSize()` returns 10 instead of 6. Each row is 16 px with a 2 px gap, so
ten rows add 180 px, close to four of Home Assistant's 50 px card rows.

### DD5. Test surface

Rows keep `data-row` with their sensor key, so Rain chance is
`data-row="precipitation_probability"`. Shaded cells keep `data-shade`, and
arrow cells carry `data-arrow`. The label's text is the row's name.

No decision here is costly to reverse: each sits inside the card's own
source, behind the published entities.

## Risks / Trade-offs

- [Fifteen rows make the card tall on a phone] → Accepted for this story; a
  row picker is left to the visual editor (#188).
- [A fixed temperature scale shows little change on a night that stays
  within one 5 °C step, and every hour below −5 °C takes the lightest shade]
  → The hover shows each value, and one shared fixed scale lets Temperature
  and Dew point be compared by eye, which a scale fitted to each night would
  not. Matching shades only mean the two values share a 5 °C step, so the
  docs do not call them a dew warning.
- [The NWS provider fills `precipitation_probability` by the hour each value
  starts, not the hour it ends (`pierpressure/conditions/nws.py`, `_hours`),
  against `docs/night-timeline.md`] → On a pier where NWS supplies rain
  chance, the card draws it an hour early. The card follows the documented
  rule; aligning NWS is a core fix outside this change.
- [An arrow in a narrow cell is small] → It scales with the cell; at the
  card's typical width each hour is about 15 px wide.
- [happy-dom does not draw the SVG, so tests cannot prove the arrow looks
  right] → The tests assert `data-arrow` and the group's `transform`.
  `mise run dashboard-check` checks the drawing by eye.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card source; the
published entities are unchanged.
