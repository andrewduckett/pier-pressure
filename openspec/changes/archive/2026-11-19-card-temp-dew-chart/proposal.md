<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

Dew risk is the gap between the temperature and the dew point, and two rows
of blues cannot show a gap: matching shades only say that both values are in
the same 5 °C step. Andrew keeps a separate temperature and dew point chart
under the card for this. A chart inside the card puts the two lines on the
strip's time axis, so they pan with it, and every adopter gets it. It also
removes the last exception to "darker is better for observing", which #252
left on these two rows.

## What Changes

- **New:** the Temperature chart, part of the night strip. It draws a
  Temperature line and a Dew point line from
  `sensor.pierpressure_<slug>_temperature` and `_dew_point`, under the target
  lanes and above the time labels. The dusk, dawn and now lines cross it, and
  dragging or swiping on it pans the strip (D1, D4, D5).
- Each hour's point sits at the middle of its hour (D6). A line breaks at an
  hour with no value, and an hour with no value on either side is a dot
  (D7).
- A °C scale fits both lines' values across the whole pan reach, widened to
  whole 5 °C steps, with a gridline and a label at each step in the label
  column. The scale stays put while the user pans (D8).
- Temperature is orange and Dew point green, with a key in the label column
  (D9). Hovering over an hour shows both values (D10).
- A line whose sensor is missing, unavailable or has no forecast on the strip
  shows the row message beside its key entry, and hovering over it names the
  sensor. The chart keeps its place (D11).
- Both sensors still count toward how far the strip pans (D12).
- **Removed:** the Temperature and Dew point rows and their blues. The strip
  has fourteen rows, or thirteen without Cloud range. The docs and the spec no
  longer name Temperature and Dew point as the exception to "darker is better
  for observing" (D2).

Out of scope: a Dew risk row, any new sensor, and any change to the core, the
verdict document or the MQTT entities (D3). This is a change to what the card
draws and to its docs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: new requirements for the Temperature chart: where it sits,
  what it reads, where points go, gaps, the °C scale, the line colours and
  key, the hover text, the messages, and the docs. The requirement "Warmer is
  darker in Temperature and Dew point" is removed. The requirements that list
  the rows, count them or name Temperature and Dew point among the rows
  change to leave them out. The lines, panning and reach requirements change
  to cover the chart. "The docs say darker is better for observing" drops the
  exception.

## Impact

- `card/src/strip.ts`: Temperature and Dew point leave `ROWS`;
  `temperatureShade` goes; `stripReach` keeps both sensors; `buildStrip`
  adds the chart's model.
- `card/src/pierpressure-card.ts`: renders the chart as a strip row under the
  target lanes, with its styles, and stretches the lines overlay over it.
  Rendering may move to a new `card/src/chart.ts`.
- Card tests in `card/test/`: the Temperature and Dew point row tests in
  `rows.test.ts` go; the row lists and grid-row counts in `strip.test.ts`
  and `targets.test.ts` change; a new chart test file.
- `openspec/specs/night-card/spec.md`, through this change's delta.
- `docs/night-card.md` and `tests/test_night_card_doc.py`.
- No new dependency. The chart is SVG drawn with Lit's `svg` tag, as the moon
  drawing is.
