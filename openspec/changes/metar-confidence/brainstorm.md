## Story

#219 metar-confidence — confidence falls when the observed low or mid cloud contradicts this hour's forecast.
https://github.com/andrewduckett/pier-pressure/issues/219

The issue thread had no comments at either fetch.

The user pre-authorized the recommended answer to every question in this
brainstorm, so rows the agent recommended are recorded as `User`. No question
was left without a recommendation.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does the comparison need a glossary term? | No. "Agreement" stays the measure between forecasts. Specs say in plain words that the observed cloud is above this hour's forecast. No glossary edit. | User |
| D2 | Which forecast hour is compared? | The clock hour that holds the evaluation instant, read from the filled cloud series. No other hour, and never an alternate. | Evidence: #219 Scope |
| D3 | Does the check run only near or during the night? | No. It runs at any instant with a usable observation and a forecast for that hour, before dusk too. Lead time already discounts a verdict far from dusk. | User |
| D4 | Which way can the observation move confidence? | Down only, and only when the report shows more cloud than the forecast. Less cloud, a clear report or a CAVOK report never changes confidence, because a station sees only so high and can only confirm cloud. | Evidence: #216 Shared decisions |
| D5 | How much cloud does a report prove? | The largest cover of any layer with a known base at or below 12,000 ft, at the least its code allows: FEW 12.5%, SCT 37.5%, BKN 62.5%, OVC, OVX and VV 100%. Higher layers, layers with no base and other codes count for nothing. | User |
| D6 | What is it compared with? | The forecast's low and mid cloud for that hour, never high cloud. Both values must be present for the hour. Otherwise the check does not run. The design picks how the two layers combine. | Evidence: #219 Scope |
| D7 | How much does it lower confidence? | By the gap in points, observed minus forecast, rounded: under 15 changes nothing, 15 to 35 multiplies by about 0.9, over 35 by about 0.67. The bands and factors are the agreement's. | User |
| D8 | How does it combine with agreement? | It multiplies with the agreement factor after the floor. Together they never take a confidence at or above MEDIUM below MEDIUM, as agreement alone does today. | User |
| D9 | Which verdicts does it affect? | Every verdict whose confidence comes from the forecast, gated NO-GO included. Not one with no dark window, no dark time left or no cloud data, whose confidence is fixed. | Evidence: pierpressure/core/scoring.py (evaluate) |
| D10 | When is there a reason line, and what does it say? | Only when confidence is lowered: one line in the agreement line's style, naming the station, the observed and the forecast percentages, and ending `Confidence lowered.`. The design settles the exact words. | User |
| D11 | Where does the line go? | Straight after the observation line, so the report and its effect read together, and before the equipment notes. | User |
| D12 | Does the verdict document gain a field? | No. The confidence value and the reason line carry the result. A field can come later, additively. | User |
| D13 | Do the card or the narrative change? | No. Both read `confidence` and `reasons` as they are. | Evidence: openspec/specs/night-card/spec.md, openspec/specs/verdict-narrative/spec.md |
| D14 | Which existing requirements change? | "The observation changes no gate, score or confidence" now allows this factor. The confidence requirements name the observation, and the observation line is no longer always the core's last line. | Evidence: openspec/specs/night-verdict/spec.md |

## Changes from the story

- The packet asks for a reason line "when the factor applies". D10 reads that
  as "when it lowers confidence": a line for a report that agrees would repeat
  the observation line and say nothing new.
- A CAVOK report is one of the edge tests. Under D4 it never changes
  confidence, like any other clear report.

Confirmed by user: yes
