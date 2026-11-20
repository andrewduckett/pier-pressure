<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

On the night strip, every Cloud range hour looks the same: a grey column with
a dark grey bar. To find the hours where the weather forecasts disagree about
cloud, a person has to compare bar lengths one by one, or hover over each
hour. Story #298 asks that those hours stand out at a glance, so a person can
see which hours not to trust before they set up.

## What Changes

- An hour where the forecasts disagree is one where the cloud cover max minus
  the min is more than 35 points (D2). This is the same edge the core uses
  for its DISAGREE agreement band. The edge is fixed in the card; no card
  option changes it (D3).
- The Cloud range column of such an hour is amber, for example `#b58900`,
  instead of the grey `#8c8c8c`. Its bar stays the dark grey `#404040` (D1).
  This applies to every column the strip draws, panned or not (D5).
- The amber column meets the same contrast rule as the grey one: at least 3:1
  against the bar, against the light card `#ffffff` and against the dark card
  `#1c1c1c` (D1). It must also stay distinct from the Temperature line's
  orange `#d97706`.
- The hover text, the tap text and the aria-label of such an hour say the
  forecasts disagree, for example
  `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree` (D4).
  A tap needs no new item or `data-tip` key, because the column already has
  one (D6).
- `docs/night-card.md` says how to read the Cloud range row: where the bar
  sits is how cloudy, its length is how far the forecasts disagree, and an
  amber column is an hour not to trust. It says the card uses the same
  35-point edge as the verdict's agreement band (D8).

Nothing changes in the core, the verdict document or the MQTT entities (D7).
No colour on the row reads as good.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the Cloud range shades requirement gains the amber column for
  an hour where the forecasts disagree, with its threshold. The Cloud range
  contrast requirement covers the amber column too. The Cloud range hover
  requirement adds the words for such an hour. The docs requirements for the
  Cloud range row say how to read it and that its colour is grey or amber,
  never one that reads as good.

## Impact

- `card/src/strip.ts`: the Cloud range `Band` says whether its hour is one
  where the forecasts disagree, and its text adds the words.
- `card/src/pierpressure-card.ts`: the Cloud range column styles and
  `renderBand` draw such an hour's column amber.
- `card/test/range.test.ts`, and `card/test/tap.test.ts` for the tap text:
  new tests for the threshold, the colour, the contrast and the text.
- `docs/night-card.md`: the Cloud range text in the strip section.
- `openspec/specs/night-card/spec.md`: through this change's delta spec.
- No change to `pierpressure/core/`, the verdict document, the MQTT surface or
  any dependency.
