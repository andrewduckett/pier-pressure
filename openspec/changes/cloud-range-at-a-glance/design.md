<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

The card builds the Cloud range row in `cloudRange` in `card/src/strip.ts`.
For each paired hour it makes a `Band` with `low` and `high` (clamped to
0–100 by `percent`) and a `text` that holds the unclamped values.
`renderBand` in `card/src/pierpressure-card.ts` draws the band as a
`div.cell.column` with an inner `div.range`. The same element carries the
`title`, the `aria-label` and the `data-tip` key `column:<hour>`. The tap box
in `card/src/tap.ts` looks up `band.text` by that key, so any change to
`band.text` reaches hover, screen reader and tap together.

The column's grey `#8c8c8c` and the bar's `#404040` are fixed in the card's
styles. `card/test/range.test.ts` reads those styles back and checks the
contrast rule with `contrast` from `card/test/harness.ts`.

The contrast rule leaves a narrow band of usable colours. A column needs at
least 3:1 against the bar (relative luminance at least 0.254) and at least
3:1 against `#ffffff` (luminance at most 0.300). Any amber that fits is about
as light as the Temperature line's orange `#d97706` (luminance 0.279), so the
two can differ only by hue.

## Goals / Non-Goals

**Goals:**

- Decide "the forecasts disagree" once per hour, in the strip model, so the
  colour and the words can never disagree with each other.
- Keep hover, screen reader and tap on the one `band.text`.

**Non-Goals:**

- No new strip item, tip key or tap handling.
- No change to how the core computes the agreement band, and no attempt to
  match its rounding (see Risks).
- No theme-aware colours: the row keeps fixed colours, as it does today.

## Test Seams

- **Primary test seam:** the mounted card in `card/test/range.test.ts`. Its
  tests mount the card with `mountCard`, read the Cloud range columns with
  `columns`, and read the styles with `declarations` and `background`. This
  covers the threshold, the colour, the contrast and the hover and
  screen-reader text.
- **Existing seams reused:** the tap table in `card/test/tap.test.ts`, for
  one case where a tap shows the disagree text; and
  `tests/test_night_card_doc.py` for the docs requirements, next to the
  existing `grey` and `agree` checks.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's Cloud range row only: `card/src/strip.ts`,
  `card/src/pierpressure-card.ts`, their tests, and `docs/night-card.md`. No
  change to the core, the verdict document or MQTT.

## Decisions

### DD1: The `Band` carries a `disagree` flag

`cloudRange` sets `disagree: boolean` on each `Band`, and appends
`, the forecasts disagree` to its `text` when it is true. `renderBand` adds a
`disagree` class to the column when the flag is set.

- Alternative: `renderBand` works out the gap from `band.low` and
  `band.high`. Rejected: the text is built in `strip.ts`, so the rule would
  live in two places and could drift.
- Alternative: an inline `background-color` style. Rejected: the tests read
  colours from the stylesheet, and a class keeps every Cloud range colour in
  one place.

### DD2: The gap is taken on the clamped values, with a small tolerance

The flag is `high - low > DISAGREE_GAP + 1e-9`, with `low` and `high` the
clamped values the bar is drawn from, and `DISAGREE_GAP = 35` as a named
constant in `strip.ts`. Its comment names the core's `MIXED_MAX_GAP` in
`pierpressure/core/scoring.py` as the source of the number.

- Clamped, not raw: the colour then always matches the bar length a person
  sees. Raw values outside 0–100 do not occur in practice, so this choice
  only settles the spec's edge case.
- The tolerance stops floating-point error from making an exact 35-point gap,
  such as 35.1 to 70.1, read as more than 35.
- Alternative: import the number from the core. Not possible: the card is
  TypeScript and only reads published entities.

### DD3: The amber is `#b58900`

`.column.disagree { background-color: #b58900; }`. Its contrast is 3.23
against the bar, 3.21 against `#ffffff` and 5.31 against `#1c1c1c`, which
meets the rule with little room on the light card. It is the ledger's
example colour (D1).

- Alternative: a yellower amber, such as one near 54° hue, further from the
  orange. Rejected for now: the ledger names `#b58900`, and the Risks below
  are mitigated without it.

## Risks / Trade-offs

- [The amber `#b58900` (hue about 45°) and the Temperature orange `#d97706`
  (hue about 32°) are equally light and close in hue] → They never touch: the
  Cloud range row is near the top of the strip and the Temperature chart is
  under the target lanes. The chart has a key that names its colours, and
  the amber column always comes with the words "the forecasts disagree".
- [The amber and the grey column are about equally light (contrast 1.05),
  so a person who sees no colour cannot tell them apart] → The hover text,
  tap text and aria-label say the forecasts disagree (D4), and the bar's
  length still shows the gap.
- [The light-card contrast is 3.21, close to the 3:1 floor] → The contrast
  test in `range.test.ts` reads the colour from the styles, so any later
  change that breaks the rule fails the gate.
- [The core rounds its window-mean gap to whole points before it compares
  it with 35; the card compares one hour's gap unrounded] → The two measure
  different things anyway (a whole window versus one hour). They share the
  edge, which is what the docs promise. They differ only for a gap between
  35 and 35.5.

## Migration & Rollback

N/A. The card is rebuilt and shipped as before. Rolling back is reverting
the change; no stored state or config changes shape.
