**Why:** With the default single cloud provider, every new install shows a Cloud range row that only says "Needs two forecasts", which reads as a fault when nothing is wrong, so the card should hide the row until two forecasts give cloud.

## Story

#212 cloud-range-hides-alone — the card hides the Cloud range row when only one weather forecast gives cloud.
https://github.com/andrewduckett/pier-pressure/issues/212

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does the story fit one change? | Yes. It touches `card/src/strip.ts`, its tests, `docs/night-card.md`, its doc test and the night-card spec: about nine tasks. | Evidence: #212 Relevant code |
| D2 | When is the Cloud range row hidden? | When both sensors are in Home Assistant, neither is `unavailable`, and the two whole `forecast` lists have no paired hour. | Evidence: #212 Scope |
| D3 | What is a paired hour? | A min point and a max point with the same `datetime`, both finite numbers, in either order. A readable pair, which also needs min ≤ max, still decides whether an hour gets a column. | Evidence: plan review round 1, `card/src/strip.ts` `cloudRange` |
| D4 | Which hours does the hide rule look at? | Every point in both forecasts, not only the axis, so panning never adds or removes the row. A new state from Home Assistant can. | Evidence: #212 Scope |
| D5 | In what order are the cases checked? | `Not found` (min, then max), then `Unavailable` (min, then max), then hide, then columns or `No forecast`. The first two keep today's order. | Evidence: `card/src/strip.ts` `cloudRangeMissing` |
| D6 | What does a shown row with no column on the axis say? | `No forecast`, marked `no-forecast` like other rows, with the hover text `No hour on the strip has cloud cover from two or more forecasts`. | Evidence: #212 Scope |
| D7 | What happens to `Needs two forecasts`? | It is retired from the code, the `Missing` type, the spec and the docs. | Evidence: #212 Scope |
| D8 | What does "hidden" mean on screen? | No label, no track and no grid row. The strip has fifteen rows; the grid and the lines overlay already size from the row count. | Evidence: `card/src/pierpressure-card.ts` strip grid |
| D9 | Does `getCardSize` change? | No. It ignores the row count today, and one 32 px row is less than one 50 px card unit. | Assumption |
| D10 | If every paired hour has min above max, as during a half-applied update, what happens? | The row stays and says `No forecast` until the second sensor's update arrives, so the rows under it do not jump. | Evidence: plan review round 1, `card/src/strip.ts` `cloudRange` |
| D11 | How do the docs explain the hidden row? | The strip section says the row shows only when two or more forecasts give cloud cover. The troubleshooting item becomes "The strip has no Cloud range row", with the same two causes, and says a second provider that fails for a whole fetch hides the row too. | Evidence: #212 Scope |
| D12 | Which tests move with the docs? | `tests/test_night_card_doc.py`, which checks the docs' text. It is a docs test, not a core or MQTT change. | Evidence: `tests/test_night_card_doc.py` |
| D13 | Does this need a glossary term? | No. "Paired hour" and "readable pair" stay phrases the night-card spec defines where it uses them. | Assumption |

## Changes from the story

- The hide rule counts a paired hour whatever the order of its two values, where the issue said min ≤ max. Home Assistant applies the min and max updates one at a time. A new min can then sit above the old max at every hour, and the issue's rule would hide the row and show it again, moving every row under it. The plan review found this.

Confirmed by user: yes
