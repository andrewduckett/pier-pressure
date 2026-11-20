<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#252 strip-shades-good-bad — on every shaded row of the night strip, darker
blue means better for observing.
https://github.com/andrewduckett/pier-pressure/issues/252

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which rows change direction? | Cloud cover, Cloud low, Cloud mid, Cloud high, Humidity, Rain chance, Wind gust, Wind speed, Seeing and Transparency: darker now means better for observing. | Evidence: #252 packet, Scope |
| D2 | Does Sun altitude change? | No. It already reads darker is better: darkest at astronomical night. | Evidence: #252 packet; `card/src/strip.ts` `sunShade` |
| D3 | What happens to Temperature and Dew point? | They keep their blues, darker is warmer, until `card-temp-dew-chart` (#253) replaces them. The docs name them as the one exception. | Evidence: #251 Shared decisions |
| D4 | How is Moon altitude shaded? | By altitude alone: darkest while the moon is on or below the horizon, one step paler for every 6° it climbs. The docs say the shade ignores the moon's phase. | Evidence: #252 packet, Scope |
| D5 | Where do the flipped rows' steps fall? | Mirror today's steps: the step edges stay and the order of the seven blues reverses. Cloud 0–14% is darkest and 90%+ palest; wind under 7 km/h darkest and 42 km/h+ palest; Seeing and Transparency 1 darkest, 0.5 at `#6da7ec`, 0 palest; Moon on or below 0° darkest, above 0° to under 6° one step paler, 30°+ palest. | Assumption |
| D6 | How is the Cloud range row drawn? | Its column and bar use two greys, not blues, because the bar shows where the cloud is and how far forecasts disagree, not good or bad. Height and bar geometry stay, except the bar's width (D10). | Evidence: #252 packet; #251 Shared decisions |
| D7 | What contrast must the two greys pass? | Fixed greys: the bar at least 3:1 against its column, and the column at least 3:1 against Home Assistant's default card background in light (`#ffffff`) and dark (`#1c1c1c`) themes (WCAG 2.2 non-text contrast). | Assumption |
| D8 | What else on the strip stays as it is? | Wind direction arrows, the Moon up lane, target bars, row order, hover text and row messages. | Evidence: #252 packet, Scope |
| D9 | Which docs and specs change? | The night-card requirements that fix each row's shades, and their scenarios; "The docs describe every row", which today asks for "darker means worse"; and `docs/night-card.md` "How to read the rows": the opening, the shade table and the Cloud range text. | Evidence: #252 packet, Scope and Relevant code |
| D10 | No pair of fixed greys meets D7 on both themes when the bar touches the card: a long bar fades into one theme's card background. How is the bar kept apart from the card? | Inset the bar 1 px from each side of its column, so the column frames it on both themes. The bar's height and vertical extent stay; only its width shrinks by 2 px, from about 9 px to 7 px on a phone. | Assumption |

## Changes from the story

None. Highlighting long Cloud range bars is already its own story,
`cloud-range-at-a-glance` (#298).

Confirmed by user: yes
