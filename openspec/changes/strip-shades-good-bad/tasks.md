<!-- Plain language: Each task must make sense to an agent and reviewer without the planning conversation. Name an observable outcome, its location when needed, and how to verify it. Preserve checkbox syntax and tags. -->

Read design.md first. Shade hex values and scenarios come from
`specs/night-card/spec.md` in this change. Rename each test's `describe` to
its requirement's new name, such as "less cloud is darker". The Sun altitude,
Temperature and Dew point tests must pass unchanged throughout.

## 1. Rows that read darker as better

- [ ] 1.1 [easy] Every percent row (Cloud cover, Cloud low, Cloud mid, Cloud high, Humidity, Rain chance) shades step 0 as the darkest blue: 0% `#0d366b`, 44% `#256abf`, 100% `#cde2fb`, the edges 14/15/89/90%, and −5% and 120% at the palette's ends. Add `darkestFirst(step)` beside `blue(step)` in `card/src/strip.ts` and call it from `percentShade` (design decision 1). Update the cloud tests in `card/test/strip.test.ts` and the Humidity and Rain chance tests in `card/test/rows.test.ts` (verify: `npm --prefix card test -- test/strip.test.ts test/rows.test.ts`)
- [ ] 1.2 [easy] The Moon altitude row pales as the moon climbs: −10, 0, 3, 6, 12, 18, 24, 30 and 60° shade `#0d366b`, `#0d366b`, `#184f95`, `#256abf`, `#3987e5`, `#6da7ec`, `#9ec5f4`, `#cde2fb`, `#cde2fb`; and 12° shades `#3987e5` whether the verdict's `moon.illumination` is `0` or `1`. `moonShade` calls `darkestFirst`; update its comment (verify: `npm --prefix card test -- test/rows.test.ts`)
- [ ] 1.3 [easy] Less wind is darker: Wind gust 0, 6.9, 7, 41 and 42 km/h shade `#0d366b`, `#0d366b`, `#184f95`, `#9ec5f4`, `#cde2fb`, and Wind speed 21 km/h stays `#3987e5`. `windShade` calls `darkestFirst`; update its comment (verify: `npm --prefix card test -- test/rows.test.ts`)
- [ ] 1.4 [easy] Better seeing and transparency are darker: Seeing 1, 0.8, 0.5 and 0 shade `#0d366b`, `#184f95`, `#6da7ec`, `#cde2fb`, and Transparency 1.2 shades `#0d366b`. `qualityShade` calls `darkestFirst`; its comment no longer says darker is worse, and the `BLUES` comment says which rows read it darkest first (verify: `npm --prefix card test -- test/rows.test.ts`)

## 2. Cloud range greys

- [ ] 2.1 [easy] Each Cloud range column is `#8c8c8c` and each range bar `#404040`, and a new test in `card/test/range.test.ts` computes WCAG 2.2 contrast ratios from the stylesheet's two `background-color` values: bar against column, column against `#ffffff`, and column against `#1c1c1c`, each at least 3 (design decisions 2 and 4). Write the contrast test first; it fails on today's `#cde2fb` and `#256abf`. Change `.column` and `.range` in `card/src/pierpressure-card.ts` and the existing styles test (verify: `npm --prefix card test -- test/range.test.ts`)
- [ ] 2.2 [easy] Each range bar is inset 1 px from both sides of its column: `.range` declares `left: 1px` and `right: 1px` in place of `left: 0` and `right: 0`, and the bar's inline `bottom` and `height` stay as the existing range tests assert (design decision 3). Update the column's stylesheet comment (verify: `npm --prefix card test -- test/range.test.ts`)

## 3. The docs read darker as better

- [ ] 3.1 [easy] The opening of "How to read the rows" in `docs/night-card.md` says darker means better for observing on every shaded row, with Temperature and Dew point as the one exception, where darker is warmer; the shade table lists Darkest before Lightest for each row; and the page no longer says "darker means worse". In `tests/test_night_card_doc.py`, replace the term "darker means worse" with "darker means better", add "exception" and "warmer", and add a test that "darker means worse" is gone (design decision 5) (verify: `uv run pytest tests/test_night_card_doc.py`)
- [ ] 3.2 [easy] The docs say the Moon altitude shade ignores the moon's phase: a doc test asserts the word "phase" in "How to read the rows" (verify: `uv run pytest tests/test_night_card_doc.py`)
- [ ] 3.3 [easy] The Cloud range paragraph names a grey column and a darker grey bar, says the row is grey because it shows how far the forecasts agree, not good or bad, and no longer says "light blue" or "dark blue". Doc tests assert "grey" and "agree" before "If something looks wrong", and that the Cloud range text has no "blue" (verify: `uv run pytest tests/test_night_card_doc.py`)

## 4. Integration [depends-on: 1, 2, 3]

- [ ] 4.1 [easy] The full CI gate passes: specs, ruff, mypy, pytest, and the card's type check, tests and build (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
