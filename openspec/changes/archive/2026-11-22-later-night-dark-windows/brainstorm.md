<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#318 later-night-dark-windows — the night strip draws dusk and dawn on every night it pans to, https://github.com/andrewduckett/pier-pressure/issues/318

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which nights are later nights, and how many? | One per local solar day after the selected night, in date order, up to three. | Assumption |
| D2 | When does a later night's solar day count as reached? | While that solar day starts before the end of the last hour a provider returned for a variable the timeline shows; so when every provider fails, there are no later nights. | User |
| D3 | How does the verdict document carry later nights? | A `later_nights` list after `observation`; each entry holds a `dark_window` in the top-level shape, with null bounds on a night with no astronomical darkness. Tonight's fields are unchanged and not repeated. | Assumption |
| D4 | Is `later_nights` always in the document, even with no later nights? | Yes, always present, as an empty list when there are none, like `targets`. | User |
| D5 | Do the Verdict sensor's attributes carry `later_nights`? | No, they leave it out, as they leave out `timeline`, to stay under Home Assistant's 16 KiB attribute limit. | Assumption |
| D6 | How are later nights delivered to Home Assistant? | Each pier gets Night 2 to Night 4 sensors (`sensor.pierpressure_<slug>_night_<n>`): state is that night's dusk as a timestamp, attributes hold its entry, and the sensor is unavailable when its night is not in `later_nights`. | Assumption |
| D7 | What does a Night sensor show when its night has no astronomical darkness (null dusk and dawn)? | State unknown; the sensor stays available, with the entry's null bounds in its attributes. Unavailable means only that the night is not in `later_nights`. | User |
| D8 | How does the card draw later nights' dusk and dawn? | The same dashed grey dusk and dawn lines and hover text as tonight, drawn even when tonight has no dark window and the axis falls back to the browser's clock; a later night with no darkness gets no lines and no note. | User |
| D9 | What does the glossary entry for *Later night* say? | A night after the selected night, one per local solar day, that the forecast reaches, up to three; each carries its own dark window and no verdict, score or confidence. Scope: the verdict document, its delivery and dashboards. Code and specs use `later_nights`. Written to `openspec/glossary.md`. | User |

D1, D3, D5 and D6 come from the Shared decisions in epic #299, which `lets-go` accepted on the shaping step's recommendation; the user did not decide them.

## Changes from the story

- **Night count rule changed (D2).** The story counted a later night while its solar day starts before the timeline's last hour ends. The selected night's own hours always run to the next solar noon, so that rule would always reach a second night, even when every provider fails, which contradicts epic #299. The rule now counts only hours a provider returned for a variable the timeline shows.
- **Added: `later_nights` is always present (D4),** as an empty list when there are none.
- **Added: a Night sensor for a night with no darkness reports state unknown and stays available (D7).** The story only defined the dusk state and the unavailable case.
- **Clarified: the card draws later nights' lines even when tonight has no dark window (D8).** Tonight's fields and the card's opening axis still do not change.
- **Added: the glossary entry for *Later night* (D9).** It replaces the tentative term in epic #299.

Nothing was split out.

Confirmed by user: yes
