<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#298 cloud-range-at-a-glance — hours where the forecasts disagree on cloud
stand out on the night strip.
https://github.com/andrewduckett/pier-pressure/issues/298

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How does an hour where the forecasts disagree stand out on the Cloud range row? | Its whole column is amber, for example `#b58900`, and its bar stays the grey `#404040`. Every other column stays the grey `#8c8c8c`. No amber bar keeps #252's 3:1 contrast against the grey column; an amber column does against the bar (3.23), `#ffffff` (3.21) and `#1c1c1c` (5.31). | Assumption |
| D2 | What gap marks an hour as one where the forecasts disagree? | The max minus the min is more than 35 points, the core's DISAGREE band edge (`MIXED_MAX_GAP` in `pierpressure/core/scoring.py`). A gap of exactly 35 does not count. | Assumption |
| D3 | Can people change the threshold, for example with a card option? | No. The card fixes it, as the core fixes its own. | Assumption |
| D4 | Do the hover text, the tap text and the aria-label of such an hour say so in words? | Yes, for example `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`, so people who cannot see the colour, screen-reader users included, get the warning. The design can still change the wording. | Assumption |
| D5 | Which columns can be amber? | Any Cloud range column the strip draws, on any hour of the axis, panned or not, by the rule in D2. | Evidence: #298 packet, Scope |
| D6 | Does tapping need a new item or key? | No. The column already has a `data-tip` key (`column:<hour>`, `card/src/tap.ts`), so a tap shows the new text without one. | Evidence: `card/src/tap.ts`, `card/src/pierpressure-card.ts` (`renderBand`) |
| D7 | What stays out of scope? | Any change to how the core builds the cloud cover min and max or the verdict's confidence, and green or any colour that reads as good. | Evidence: #298 packet, Scope (out) |
| D8 | Which documents change? | The night-card spec (`openspec/specs/night-card/spec.md`): the Cloud range shades, contrast, hover and docs requirements. And `docs/night-card.md`: how to read the row — where the bar sits is how cloudy, its length is how far the forecasts disagree, an amber column is an hour not to trust. | Evidence: #298 packet, Scope |

## Changes from the story

- Changed: the story said to draw the long bars in a warning colour. D1 colours
  the column instead, because no amber bar meets #252's contrast rule for the
  bar against its column.
- Added: the hover text, tap text and aria-label say the forecasts disagree
  (D4), so the warning does not rely on colour alone.

Confirmed by user: yes
