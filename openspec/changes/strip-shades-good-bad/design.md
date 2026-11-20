<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

All the strip's shading lives in the dashboard card, `card/`. No core,
verdict or MQTT code changes.

- `card/src/strip.ts` holds the seven blues as `BLUES`, lightest first, and
  `blue(step)`, which clamps a step to 0–6 and returns `BLUES[step]`. Each
  shaded row has a shade function: `percentShade` (the four cloud rows,
  Humidity, Rain chance), `moonShade`, `windShade`, `qualityShade` (Seeing,
  Transparency), `sunShade` and `temperatureShade`. Each computes a step,
  where step 0 is the lightest today.
- `card/src/pierpressure-card.ts` styles the Cloud range row in its
  stylesheet: `.column` has `background-color: #cde2fb`, and `.range` has
  `left: 0; right: 0; background-color: #256abf`. `renderBand` sets only the
  bar's `bottom` and `height` inline.
- Tests: `card/test/rows.test.ts` and `card/test/strip.test.ts` assert each
  cell's `data-shade`. `card/test/range.test.ts` reads the stylesheet as text
  with `cardStyles()` and its `declarations(selector)` helper, because the
  test DOM does no layout. `tests/test_night_card_doc.py` asserts words in
  `docs/night-card.md`, including "darker means worse".

## Goals / Non-Goals

**Goals:**

- Mirror the flipped rows' shades with no change to any step edge (D5).
- Make the Cloud range greys meet D7 on both default themes, with the bar
  inset 1 px (D10), and prove the contrast in a test.
- Keep Sun altitude, Temperature and Dew point exactly as they are.

**Non-Goals:**

- No new palette, no theme variables, no change to `BLUES`.
- No change to the Cloud range bar's `bottom` and `height` arithmetic.
- No highlighting of long Cloud range bars (#298).

## Test Seams

- **Primary test seam:** the card harness, `mountCard` in
  `card/test/harness.ts`, run by Vitest. It mounts the card with Home
  Assistant states and reads each cell's `data-shade` and the stylesheet
  text.
- **Existing seams reused:** `card/test/rows.test.ts`,
  `card/test/strip.test.ts` and `card/test/range.test.ts` for the card;
  `tests/test_night_card_doc.py` (pytest) for the docs page.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's shade functions in `card/src/strip.ts`, two
  stylesheet rules in `card/src/pierpressure-card.ts`, their tests, and
  `docs/night-card.md` "How to read the rows". The verdict document, MQTT
  entities and core are untouched.

## Decisions

### 1. Mirror with one helper, not a second palette

Add `darkestFirst(step)` beside `blue(step)` in `card/src/strip.ts`. It
returns `blue(6 − step)`; `blue` already clamps, so a value outside its row's
range still takes the nearest end of the palette. 120% cloud is step 8, so
`blue(−2)`, the lightest; −5% is step −1, so `blue(7)`, the darkest.
`percentShade`, `moonShade`, `windShade` and `qualityShade` call it in place
of `blue`; their step formulas stay as they are. `sunShade` and
`temperatureShade` keep calling `blue`. The spec's "Values outside 0 to 100"
and "A quality above 1" scenarios pin the ends.

Alternatives:

- A reversed copy of `BLUES`: two arrays that must stay in step, for no gain.
- Rewriting each step formula as `6 − …`: four formulas change, and each
  needs its own clamp to stay right at the ends.

Update the comments on `BLUES` and the four functions to say which end is
darkest. `qualityShade`'s comment says "darker is worse" today.

### 2. The Cloud range greys: column `#8c8c8c`, bar `#404040`

A dark bar on a lighter column reads as today's row does, so a user who knows
the row today reads it the same way. Measured as WCAG 2.2 contrast ratios:

| Pair | Ratio | D7 needs |
|---|---|---|
| Bar `#404040` against column `#8c8c8c` | 3.08:1 | 3:1 |
| Column against light card `#ffffff` | 3.36:1 | 3:1 |
| Column against dark card `#1c1c1c` | 5.07:1 | 3:1 |

The bar against the dark card is only 1.64:1. The inset (decision 3) is what
keeps that from mattering.

The colours stay literal hex values in the stylesheet, as `#cde2fb` and
`#256abf` are today. Home Assistant theme variables were ruled out by D7.

Alternative: a light bar on a darker column (`#c4c4c4` on `#6c6c6c`). It
meets D7 too, but inverts how the row reads today, for no gain once the bar
is inset.

### 3. Inset the bar with `left: 1px; right: 1px`

Change `.range` from `left: 0; right: 0` to `left: 1px; right: 1px`. The
column frames the bar on both sides, so a bar from 0% to 100% still reads
against the column, not the card. `renderBand`'s inline `bottom` and
`height` do not change, so the bar's vertical extent stays (D10). The column
keeps `overflow: hidden` and its 2 px rounded corners.

### 4. Test the contrast from the stylesheet

`card/test/range.test.ts` already reads `.column` and `.range` declarations.
Add a small WCAG 2.2 relative-luminance and contrast-ratio function to that
test file, read the two `background-color` values with `declarations`, and
assert the three ratios are each at least 3. The test then fails if someone
changes a grey to one that breaks D7, not only if they change the hex.

The function is test code only. The card never computes contrast at run
time.

### 5. The docs: one rule, one exception

Rewrite the opening of "How to read the rows" in `docs/night-card.md` to say
that on every shaded row darker means better for observing, with Temperature
and Dew point the one exception, where darker is warmer. Reorder the shade
table's columns to Darkest then Lightest, so each row reads best first. Add
to the Moon altitude row that the shade ignores the moon's phase. Rewrite the
Cloud range paragraph to name a grey column and a darker grey bar, and say
the row is grey because it shows agreement, not good or bad.

In `tests/test_night_card_doc.py`, replace the term "darker means worse"
with "darker means better", add "warmer", "phase" and the grey checks, and
add a test that "darker means worse" is gone.

## Risks / Trade-offs

- [Users who know today's strip read a dark hour as bad] → The docs'
  opening states the new rule first, and the pull request says the shades
  are reversed.
- [The bar is 2 px narrower, about 7 px on a phone] → Each column is still
  a whole hour wide; the bar's height, which carries the information, is
  unchanged. D10 accepted this trade.
- [A user's custom theme has a card background near `#8c8c8c`] → D7 fixes
  contrast only for Home Assistant's default themes. The bar still shows
  against its column on any theme.
- [The bar against its column has little margin, 3.08:1] → The contrast
  test fails if a later edit drops it below 3:1.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card release; the
core and its entities are untouched.
