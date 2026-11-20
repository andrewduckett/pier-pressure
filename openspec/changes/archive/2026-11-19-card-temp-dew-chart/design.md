<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

All of this change is in the dashboard card, `card/`, and its docs. No core,
verdict or MQTT code changes.

- `card/src/strip.ts` builds the strip's model. `buildStrip` returns a
  `Strip` with `rows`, `moonUp`, `targets`, `lines` and `labels`, all placed
  on an `axis` in epoch milliseconds. `ROWS` lists each row with its key,
  label, unit and shade function; Temperature and Dew point use
  `temperatureShade`. `stripReach` walks the forecasts of every `ROWS` key
  plus `cloud_cover_min` and `cloud_cover_max`. `forecastOf` hides an
  unavailable sensor's forecast, and `missing` picks `Not found`,
  `Unavailable` or `No forecast` for a row with no cell.
- `card/src/pierpressure-card.ts` renders the strip as one CSS grid: a
  `max-content` label column and a `1fr` track column. Grid row 1 holds the
  line labels, then the rows, the Moon up lane, the target lanes and the time
  labels. The `.lines` overlay spans `grid-row: 2 / <laneEnd>`, so the dusk,
  dawn and now lines stop under the last lane. Everything is placed in
  percent of the axis with `offset` and `share`, so the strip reflows with
  the card's width. The pointer, wheel and key handlers sit on the `.strip`
  element, so any child of the strip pans it. The moon drawing already uses
  Lit's `svg` tag.
- Tests run in Vitest on happy-dom, which does no layout. `card/test/harness.ts`
  mounts the card with Home Assistant states; tests read `data-*`
  attributes, `title` text and inline styles. `card/test/range.test.ts` has a
  WCAG luminance and contrast helper. `tests/test_night_card_doc.py` asserts
  words in `docs/night-card.md`.

## Goals / Non-Goals

**Goals:**

- Draw the Temperature chart as one more grid row of the strip, so the time
  axis, the overlay lines and the pan input serve it with no new mechanism.
- Keep the chart's maths in the pure model (`strip.ts`), so tests can drive
  it through the existing harness, and keep the SVG markup in its own module.
- Remove the Temperature and Dew point rows and `temperatureShade` cleanly,
  with the reach unchanged.

**Non-Goals:**

- No charting library, and no new dependency.
- No Dew risk row or dew warning, and no new sensor (D3).
- No change to the card size Home Assistant reads (see decision 8).
- No smoothing or interpolation between points (D7).

## Test Seams

- **Primary test seam:** the card harness, `mountCard` in
  `card/test/harness.ts`, run by Vitest. A new `card/test/chart.test.ts`
  mounts the card with temperature and dew point forecasts and reads the
  chart's `data-*` attributes, `title` text and inline styles.
- **Existing seams reused:** `card/test/rows.test.ts`, `strip.test.ts`,
  `targets.test.ts` and `pan.test.ts` for the row lists, grid rows, overlay
  span, reach and drag; `card/test/range.test.ts`'s contrast helper, moved to
  `harness.ts` so both test files share it; `tests/test_night_card_doc.py`
  (pytest) for the docs page.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the strip model in `card/src/strip.ts`, the strip's
  rendering and stylesheet in `card/src/pierpressure-card.ts`, a new
  `card/src/chart.ts`, the card's tests, `docs/night-card.md` and its doc
  test. One subsystem on established patterns. The verdict document, MQTT
  entities and core are untouched.

## Decisions

### 1. The chart's model lives in `buildStrip`

`Strip` gains a `chart` field, built in `strip.ts` by a `temperatureChart`
function that `buildStrip` calls with the states, pier, axis and clock:

```ts
interface ChartPoint { hour: number; at: number; value: number } // at: hour + 30 min
interface ChartLine {
  key: "temperature" | "dew_point";
  label: "Temperature" | "Dew point";
  colour: string;
  segments: Array<[ChartPoint, ChartPoint]>;
  dots: ChartPoint[];
  missing?: Missing;
}
interface ChartHour { hour: number; from: number; to: number; text: string }
interface TemperatureChart {
  scale?: { low: number; high: number }; // °C, multiples of 5
  lines: ChartLine[];                    // Temperature, then Dew point
  hours: ChartHour[];                    // hover areas
}
```

Building it in `strip.ts` reuses `forecastOf`, `missing`, `readTime`,
`hourlyValues` and `clock` with no new exports and no import cycle. The
model is plain data, so a test can assert it through the rendered
attributes.

How each part is computed:

- **Points (D6).** For each line, read `hourlyValues(forecastOf(entity))`.
  Keep each hour `h` with a finite number whose segment can reach the axis:
  `h + 2 h > axis.start` and `h − 1 h < axis.end`. That is every hour that
  overlaps the axis, plus the hour on each side.
- **Segments and dots (D7).** Walk the kept hours in order. Join `h` to
  `h + 1 h` when both hold a number. A kept hour joined to neither neighbour
  is a dot. A neighbour outside the kept window still counts as "holds a
  number" when its forecast holds one, so a point next to the window's edge
  is not drawn as a false dot.
- **Message (D11).** When no hour that overlaps the axis holds a number, set
  `missing` with the existing `missing(entityId, entity)`.
- **Scale (D8).** Over both lines' whole forecasts (every readable
  `datetime`, unavailable sensors left out by `forecastOf`), take the lowest
  and highest number. `low = floor(min / 5) × 5`, `high = ceil(max / 5) × 5`,
  and when `high − low < 10`, `high = low + 10`. No number at all leaves
  `scale` undefined.
- **Hover areas (D10).** One per hour that overlaps the axis and holds a
  number on either line, with `from` and `to` cut at the axis as a cell's
  are. The text is `The hour from <HH:MM>: ` plus `Temperature <v> °C` and
  `Dew point <v> °C`, joined by `, `, each left out when its line has no
  number. Values are written as JavaScript writes the number, as the row
  hover text does today.

Alternative: a separate `chart.ts` model that the card calls beside
`buildStrip`. It would need `forecastOf` and `missing` exported from
`strip.ts`, and the card would have to pass the axis between two builders.

### 2. The SVG markup lives in a new `card/src/chart.ts`

`chart.ts` exports `renderChart(chart, axis)`, returning the chart's grid
row: a label cell and a track. `pierpressure-card.ts` is 845 lines; the
chart's markup and its few helpers would add about 100 more to it. `offset`,
`share`, `iso`, `hourPlace` and `renderMissing` move to `chart.ts` or a small
shared module, whichever keeps the imports one-way (`pierpressure-card.ts` →
`chart.ts`).

### 3. Percent coordinates, not a stretched `viewBox`

The track holds an absolutely positioned `<svg>` that fills it, with
`overflow: hidden` so lines are cut at the axis ends. Each segment is a
`<line>` and each dot a `<circle>`, with `x` in percent of the axis
(`offset(at, axis)`) and `y` in percent of the scale
(`(high − value) / (high − low) × 100`). Gridlines are `<line>` elements from
`x1="0"` to `x2="100%"`.

SVG accepts percent for `<line>` and `<circle>` coordinates, so the chart
reflows with the card exactly as the cells do, with the same `offset` maths.

Alternative: one `<polyline>` per run with `viewBox="0 0 1000 100"` and
`preserveAspectRatio="none"`. Polyline points cannot be percent, so the
`viewBox` must stretch, which turns dots into ellipses and thickens strokes
unless every element sets `vector-effect`. More markup to test, no gain.

Each element carries test hooks: `data-series` (`temperature` or
`dew_point`), `data-from` and `data-to` on a segment and `data-at` on a dot
(ISO times of the mid-hours), and `data-celsius` on a gridline and a scale
label. The `<svg>` is `aria-hidden`; the hover areas carry the text, as
cells do.

### 4. Hover areas are cells

Each `ChartHour` renders as a `div.cell.hour` placed with `hourPlace`, the
full height of the track, with `title` and `aria-label` set to its text and
`data-hour` to its ISO hour. It sits above the `<svg>` in z-order and has no
background, so it shows nothing until hovered. Reusing `hourPlace` keeps the
2 px gaps and the axis-end cut the cells have.

### 5. The track's height is 16 px per 5 °C step

The track's inline style sets `height: <(high − low) / 5 × 16>px`, or `32px`
with no scale. One step is the height of one row, so a typical night of
three or four steps is 48 to 64 px. The minimum span of 10 °C (two steps)
keeps the key's two lines, 16 px each, inside the label cell.

### 6. The label cell holds the key and the scale side by side

The label cell is `display: grid; grid-template-columns: max-content
minmax(40px, max-content); column-gap: 8px`, as tall as the track:

- Left: the key, two lines of 16 px from the top. Each line is a 12 × 3 px
  swatch in the line's colour, the name, and the row message from
  `renderMissing` when the line has one.
- Right: the scale labels, `<value> °C` at `0.75em`, absolutely positioned
  at each gridline's `top` percent, right-aligned. Boundary labels are
  edge-aligned to stay within the row: the top label (`high`, `top: 0%`) uses
  `translateY(0)`, the bottom label (`low`, `top: 100%`) uses
  `translateY(-100%)`, and interior labels use `translateY(-50%)`, preventing
  vertical protrusion into adjacent lanes or rows.

The strip's label column is `max-content`, so it widens to fit this cell:
about 40 px for the scale labels (reserved by `minmax(40px, max-content)` so
absolutely positioned labels do not collapse the column width), and more
while a message shows. D8 and D11 put both the scale and the messages in the
label column; a wider label column is the cost.

Alternative: scale labels inside the track at its left edge. It keeps the
label column narrow but breaks D8, and the labels would cover the first
hours' lines.

### 7. Colours: Temperature `#d97706`, Dew point `#15803d`

WCAG 2.2 contrast ratios, measured:

| Colour | Against `#ffffff` | Against `#1c1c1c` |
|---|---|---|
| Temperature `#d97706` | 3.19:1 | 5.35:1 |
| Dew point `#15803d` | 5.02:1 | 3.40:1 |

The two differ in lightness too (1.57:1 against each other), which helps a
reader with red-green colour blindness, and the dew point is normally below
the temperature. Lines are 2 px wide with round caps, dots have a radius of
2.5 px. Gridlines are `#898781` at 40% opacity, 1 px, so they stay behind
the lines on both themes. The colours stay literal hex values, as the
Cloud range greys are.

A test in `chart.test.ts` reads the two colours from the rendered key
swatches and asserts the four ratios with the shared contrast helper, so a
later colour change that breaks the spec fails a test.

### 8. The card size stays as it is

`getCardSize` still reports 10 plus the lanes and reasons. The chart
replaces two rows of 16 px plus their gaps (36 px) with a track of 32 to
64 px on a typical night, a net change under one of Home Assistant's 50 px
size units. The spec's size requirement does not change.

### 9. The grid gains one row, and the overlay reaches it

In `renderStrip`, `gridRows` becomes `rows + targets + 4` and `laneEnd`
becomes `rows + targets + 4`, so the `.lines` overlay ends under the chart,
above the time labels. The chart row is a `.row` with `data-chart="temperature"`,
rendered after the target lanes and before the time labels. Its track is
inside `.strip`, so dragging, swiping and the wheel pan from it with no
handler changes. `data-chart`, not `data-row` or `data-line`, keeps the
existing `cells()` and `line()` test helpers from matching it.

### 10. Removing the rows

Delete the `temperature` and `dew_point` entries from `ROWS` and the
`temperatureShade` function. Update the `BLUES` comment: only Sun altitude
reads the blues lightest first. `stripReach` adds `temperature` and
`dew_point` to its key list (D12). The two harness constants `TEMPERATURE`
and `DEW_POINT` stay; the chart tests use them.

### 11. The docs

In `docs/night-card.md`: drop Temperature and Dew point from the rows table
and the shade table; drop the exception sentence and the "same scale"
paragraph; add a "The Temperature chart" subsection after the target lanes
covering the spec's docs requirement; extend "The lines" to say they cross
the Temperature chart; and change "On a night with no targets at all, the
strip ends at the Moon up lane" to say the Temperature chart follows the
Moon up lane. In `tests/test_night_card_doc.py`: drop the two rows from
`_ROWS`, drop "exception", "warmer" and "same scale" from the terms, add a
test that "How to read the rows" names no exception, and add the chart's
terms.

## Risks / Trade-offs

- [The label column widens by about 40 px, so every row's track is
  narrower, most on a phone] → The scale labels are short (`-5 °C`); the
  messages show only when a sensor fails. A later story can move the scale if
  users find the track too narrow.
- [Orange and green can look alike to a reader with red-green colour
  blindness] → The two colours differ in lightness, the Dew point line is
  normally the lower one, and hovering names both values.
- [A forecast with an extreme value makes the chart tall, such as 128 px for
  a 40 °C span] → The height follows the data the user has, and the scale
  stays put while panning. No cap: a cap would need a rule for clipped
  values that the ledger does not give.
- [Temperature and dew point can come from different weather sources, so the
  dew point line can cross above the temperature] → The chart draws the data
  as it is; the docs say the dew point line is normally the lower one.
- [A lone dot in an hour that the axis end cuts before its middle is cut
  off] → Its hover area still shows the value, and the line message stays
  off because the hour overlaps the axis.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card release; the
core and its entities are untouched.
