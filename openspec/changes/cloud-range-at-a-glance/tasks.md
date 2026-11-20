<!-- Plain language: Each task must make sense to an agent and reviewer without the planning conversation. Name an observable outcome, its location when needed, and how to verify it. Preserve checkbox syntax and tags. -->

Read design.md first. Texts, colours and boundary cases come from
`specs/night-card/spec.md` in this change. "An hour where the forecasts
disagree" is an hour whose clamped cloud cover max minus min is more than 35
points (design decision DD2). The card tests mount the card with `mountCard`
from `card/test/harness.ts`; `card/test/range.test.ts` already has the
`columns`, `declarations` and `background` helpers and the contrast tests to
extend.

## 1. The Cloud range column

- [x] 1.1 [medium] A Cloud range column carries the class `disagree` exactly when its hour is one where the forecasts disagree: min and max 20 and 70, 20 and 55.5, and 10 and 90 at an hour reached by pressing the Right arrow key with the strip focused, each have it; 20 and 55, 35.1 and 70.1, 40 and 70, and -5 and 31 do not. Add a `disagree` flag to `Band` in `card/src/strip.ts`, set in `cloudRange` from the clamped `low` and `high` against a `DISAGREE_GAP = 35` constant with a `1e-9` tolerance, whose comment names `MIXED_MAX_GAP` in `pierpressure/core/scoring.py`; `renderBand` in `card/src/pierpressure-card.ts` adds the class (design decisions DD1 and DD2) (verify: `npm --prefix card test -- test/range.test.ts`) (✓ `npm --prefix card test -- test/range.test.ts` passed)
- [x] 1.2 [easy] The stylesheet shades `.column.disagree` with `background-color: #b58900` and leaves `.range` at `#404040`, with no rule that recolours a range bar inside a `disagree` column; the contrast tests show at least 3:1 for `#404040` against the `.column.disagree` colour and for that colour against `#ffffff` and `#1c1c1c`. Say in the style's comment why the column, not the bar, turns amber (design decision DD3) (verify: `npm --prefix card test -- test/range.test.ts`) (✓ `npm --prefix card test -- test/range.test.ts` passed)
- [x] 1.3 [easy] A Cloud range column whose hour is one where the forecasts disagree has the `title` and `aria-label` `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree` for min and max 20 and 70 at 2026-10-31T21:00:00Z with Home Assistant's time zone `UTC`; for 20 and 55 they stay `Cloud range, the hour from 21:00: 20% to 55%`. Append the words to `Band.text` in `cloudRange` (design decision DD1) (verify: `npm --prefix card test -- test/range.test.ts`) (✓ `npm --prefix card test -- test/range.test.ts` passed)
- [ ] 1.4 [easy] A tap on the Cloud range column for min and max 20 and 70 at 2026-10-31T21:00:00Z shows a `.tip` box that reads `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`. Add a test case with a disagreeing fixture next to the existing Cloud range column case in `card/test/tap.test.ts`; no change to `card/src/tap.ts` is expected, since the tap box reads `Band.text` (verify: `npm --prefix card test -- test/tap.test.ts`)

## 2. The docs

- [ ] 2.1 [parallel] [medium] The Cloud range paragraph in the "How to read the rows" part of `docs/night-card.md` says the bar is grey and the column grey or amber, because the row shows how far the forecasts agree, not whether an hour is good or bad; that where the bar sits is how cloudy and its length is how far the forecasts disagree; that an amber column marks an hour where the forecasts disagree by more than 35 points, so its cloud forecast is not to be trusted; that this is the same 35-point edge PierPressure uses when it lowers confidence because the forecasts disagree; and it gives the example hover text `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`. Extend `test_docs_cloud_range_paragraph_says_why_the_row_is_grey` and add tests for amber, 35, confidence and the example text in `tests/test_night_card_doc.py` (verify: `uv run pytest tests/test_night_card_doc.py`)

## 3. Integration [depends-on: 1, 2]

- [ ] 3.1 [easy] The full CI gate passes: specs, ruff, mypy, pytest, and the card's type check, tests and build (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
