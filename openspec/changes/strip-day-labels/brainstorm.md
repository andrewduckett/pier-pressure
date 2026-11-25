**Why:** A strip panned to a later night shows only `HH:MM` times, so nothing tells the viewer which night it shows, and since #318 and #319 the strip holds up to four nights.

## Story

#335 strip-day-labels — the night strip shows the day and date of the hours on it, https://github.com/andrewduckett/pier-pressure/issues/335

## Decisions

A day here is a calendar day in Home Assistant's time zone, as the issue's packet says. It is not the glossary's local solar day.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Where do the day labels go? | In a new row directly under the time labels; the time labels stay as they are. | Assumption |
| D2 | How does a day label stay in view when the axis shows no day start? | Each day's label sits just right of the day's start; the day in progress at the axis's left edge keeps its label pinned at that edge, hidden once the next day's label would overlap it. | Assumption |
| D3 | What does a day label say, and in which language? | Short weekday, day and short month in English, such as `Thu 26 Nov`, with the same pinned locale and Latin digits as the time labels. | Assumption |
| D4 | How far does the divider at a day's start reach? | A thin solid rule across the time-label and day-label rows only, not through the strip's other rows. | Assumption |
| D5 | Where does a day start when its clock skips midnight, as at a clock change in `America/Santiago`? | At the first instant whose date in Home Assistant's time zone differs from the instant before: usually 00:00, and 01:00 on such a day. The divider and the label go there. | Assumption |
| D6 | Do hover and tap texts, the core, the verdict document or the MQTT entities change? | No: hover and tap texts stay `HH:MM`, and the card works the days out from the axis and Home Assistant's time zone. | Evidence: #335 packet, Scope (out) |
| D7 | Where does a day's label go when its day starts too close to the axis's right end for the whole label to fit, such as `Sun 1 Nov` in the last hour shown? | Hidden until it fits whole. Its divider still shows, and so does the label pinned at the left edge, as in D2 when two labels would overlap. | Assumption |

## Changes from the story

- The packet's "a divider at each local midnight" now means the first instant of each new date (D5), so a day whose clock skips 00:00 still gets its divider and label.

Confirmed by user: yes
