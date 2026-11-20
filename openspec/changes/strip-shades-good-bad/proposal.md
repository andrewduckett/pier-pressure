<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

On a GO night, Andrew read the pale Cloud cover row as cloud. Each row's
shade shows an amount, and whether darker is good or bad changes from row to
row, so the night strip cannot be read at a glance. This story fixes that
first, with the smallest change: the same seven blues, each row turned so
that darker always means better for observing. It is the Must story of epic
#251.

## What Changes

- Cloud cover, Cloud low, Cloud mid, Cloud high, Humidity, Rain chance, Wind
  gust, Wind speed, Seeing and Transparency reverse their blues: darker now
  means better for observing (D1). Each row keeps its step edges; only the
  order of the seven blues reverses (D5).
- Moon altitude is shaded by altitude alone: darkest while the moon is on or
  below the horizon, one step paler for every 6° it climbs, palest at 30° or
  higher. The shade ignores the moon's phase (D4, D5).
- Sun altitude keeps its shades: it already reads darker is better (D2).
- The Cloud range row's column and bar change from two blues to two fixed
  greys, because the bar shows where the cloud is and how far the forecasts
  disagree, not good or bad. The bar must reach at least 3:1 contrast against
  its column, and the column at least 3:1 against Home Assistant's default
  card background in the light and dark themes. The bar is inset 1 px from
  each side of its column, so the column frames it on both themes. The row's
  height and the bar's vertical extent stay (D6, D7, D10).
- Temperature and Dew point keep their blues, darker is warmer, until
  `card-temp-dew-chart` (#253) replaces them. The docs name them as the one
  exception (D3).
- Nothing else on the strip changes: Wind direction arrows, the Moon up lane,
  target bars, row order, hover text and row messages stay as they are (D8).
- `docs/night-card.md` "How to read the rows" is rewritten around "darker is
  better": its opening, the shade table and the Cloud range text (D9).

No change touches the core, the verdict document or the MQTT entities. This
is a change to what the card draws and to its docs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the requirements that fix each row's shades change direction
  and are renamed to match ("More cloud is darker", "The Moon altitude row
  darkens as the moon climbs", "More wind is darker", "Worse seeing and
  transparency are darker", "More humidity and rain chance is darker"). The
  Cloud range row's shades become two greys ("The Cloud range row has its own
  shades and height"), with new requirements for their contrast and the bar's
  inset. "The docs describe every row" stops asking for "darker means worse",
  and new docs requirements ask for "darker is better for observing" and for
  the Cloud range row's greys.

## Impact

- `card/src/strip.ts`: the shade functions for the flipped rows
  (`percentShade`, `moonShade`, `windShade`, `qualityShade`) and their
  comments. `sunShade`, `temperatureShade` and `BLUES` stay.
- `card/src/pierpressure-card.ts`: the `.column` and `.range` colours, and
  the `.range` inset.
- Card tests in `card/test/` that assert shades, chiefly `rows.test.ts`,
  `strip.test.ts` and `range.test.ts`.
- `openspec/specs/night-card/spec.md`, through this change's delta.
- `docs/night-card.md`, "How to read the rows".
- No new dependency. Out of scope: highlighting long Cloud range bars, which
  is `cloud-range-at-a-glance` (#298), and weighting Moon altitude by
  illumination.
