**Why:** Late in the night the strip still opens 4 hours before dusk, so most of its width shows hours that are gone, and once #213 keeps only 4 past hours of Open-Meteo weather those hours open blank.

## Story

#214 strip-follows-now — once the night has started, the night strip opens 4 hours before now
(https://github.com/andrewduckett/pier-pressure/issues/214)

## Decisions

The user delegated the open questions to the agent's recommendation. Rows marked `Assumption` are those recommendations.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Where does the opening axis start? | At the later of 4 hours before `dark_window.start` and 4 hours before the browser's clock. Before dusk nothing changes. | Evidence: #214 Scope |
| D2 | Does the axis end stay at 5 hours after dawn, or does the axis keep its length and slide? | It keeps its length, 4 hours before dusk to 5 hours after dawn, and slides with its start. A fixed end would shrink the axis every minute, so a held pan would shrink too, the label step could change mid-night, a panned next night would no longer fit, and a stale verdict could end the axis before it starts. | Assumption |
| D3 | Does the opening start move each minute or snap to whole hours? | It moves with the clock each minute, as the fallback axis already does; cells cut off at an axis end are already drawn. | Evidence: `card/src/strip.ts` `stripAxis` |
| D4 | How far back can the user pan? | The reach does not change: every timeline hour a row's sensor holds, and never less than the opening axis. The user can still pan back to dusk and the start of the target windows as far as the sensors hold hours; a row with no hour there is blank or says "No forecast". | Assumption |
| D5 | What does a pan do while the opening axis moves? | A pan keeps its own start, as today. The unpanned strip follows the clock, and a pan back onto the opening axis follows it again, as `Back to tonight` does. | Evidence: night-card spec "The strip stays where the user panned it"; `panTo` in `card/src/pierpressure-card.ts` |
| D6 | Does the no-darkness fallback axis change? | No: 6 hours before now to 18 hours after. | Evidence: #214 Scope (out) |
| D7 | When is the start clock-based? | From dusk on. The core picks the night whose dawn is next, so after dawn its next verdict's dusk sets the start again. A verdict left over after dawn keeps following now, with no dusk or dawn line; a stopped process makes the Verdict sensor unavailable, and then there is no strip. | Evidence: night-verdict spec, `dark_window`; ha-delivery spec, last-will |
| D8 | Do the dusk and dawn lines need new rules? | No. They already show only while on the axis. Add a scenario for dusk off the opening axis late in the night, and drop the code comment that the opening axis always holds both. | Evidence: #214 Scope; `nightLines` in `card/src/strip.ts` |
| D9 | Does the YAML night dashboard change too? | No. Only the card's strip follows now; the YAML strip in `docs/night-dashboard.md` keeps its dusk-based span. | Assumption |
| D10 | How do the tests cope with an opening axis that depends on the clock? | The test harness pins the browser's clock before the test night's dusk unless a test pins its own. On the real clock every suite that mounts the card is now past its test night. | Evidence: `card/test/harness.ts` `mountCard`; plan review finding 3 |
| D11 | What do the docs say? | `docs/night-card.md` says the strip opens 4 hours before dusk, or 4 hours before now once the night has started, and keeps its length. The panning section keeps "opens on the judged night", which the doc tests assert. | Evidence: #214 Scope; `tests/test_night_card_doc.py` |
| D12 | What happens when the opening axis catches up with a later pan? | The strip follows the opening axis again, without moving focus, once the opening axis reaches or passes the pan's start, even if a minute's redraw was missed. The card remembers that the pan was later than the opening axis, so an earlier pan keeps its start. Otherwise the button would hide for a minute, then come back, and the strip would stay a minute behind. | Assumption (plan review finding 2) |

## Changes from the story

- The story left two questions to the brainstorm. D2 settles the axis end: it slides and keeps its length. D4 settles the reach: no change.
- Nothing is split out. The YAML night dashboard stays as it is (D9); the story names only the card.

Confirmed by user: yes
