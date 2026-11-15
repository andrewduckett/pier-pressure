**Why:** When every forecast provider fails, the timeline is empty, so the Sun altitude and Moon altitude sensors go `unknown` and the night strip loses its sky rows, even though the core computes both altitudes offline; #156 settled where the provider hours come from, so the astronomy hours can now stop depending on any provider.

## Story

#174 timeline-astronomy-always — the timeline always carries the sun and moon
for the judged night, even when every forecast fails.
https://github.com/andrewduckett/pier-pressure/issues/174

The issue has no comments.

## Decisions

The user delegated this brainstorm. The brief said to take the recommended
answer to each question, record the alternatives, and go on without asking. So
each row that code or a document did not settle is an `Assumption`, and the
rejected alternatives follow the answer. The issue's "judged night" is the
spec's **selected night**: the night whose astronomical dawn is the first at or
after the evaluation instant.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How far do the astronomy hours reach? | Every clock hour that starts inside the selected night's local solar day: from the solar noon before the night to the next solar noon, so 24 entries on an ordinary night. It always covers sunset to sunrise, and on a mid-latitude night it covers the strip's opening axis (4 hours before dusk to 5 hours after dawn, #173). The solar day is the one that holds `dark_window.start`, found with the same solar-noon search the polar-night window already uses, and it does not slide between recomputes. Rejected: sunset to sunrise (needs a new rise/set search, and leaves the strip's first hours before dusk blank); the strip's own offsets of 4 and 5 hours (ties the core to a card layout); a fixed reach such as 72 hours from now (goes past the night the story names; the strip's reach already follows whatever hours the timeline holds). | Assumption |
| D2 | Does the reach include the current hour? | Yes. When the hour that holds the evaluation instant starts before the solar day, as it does between dawn and noon, the astronomy hours start at that hour instead. So the altitude sensors have a current-hour state at every instant during an outage, which is the issue's motivation. Rejected: the solar day alone (the sensors stay `unknown` each morning of an outage). | Assumption |
| D3 | Which solar day applies when the selected night has no dark window (polar day, or a summer night that never reaches −18°)? | The solar day whose midpoint between its two noons is the first at or after the evaluation instant: tonight's until local solar midnight, then the next one. D2 still adds the hours from the current hour. Rejected: the solar day that holds the instant (from dawn to noon it covers only the night just gone, not tonight). | Assumption |
| D4 | Does continuous polar night need its own rule? | No. Its dark window already is one local solar day, so the solar day that holds `dark_window.start` is that same window. | Evidence: `pierpressure/core/sky.py` (`dark_window`, `_local_solar_day`) |
| D5 | How do the astronomy hours combine with the provider hours? | As a union, sorted, each hour once. Provider hours outside the solar day stay. Hours that only an alternate or a variable the timeline does not show covers still add no entry (#156's rule). | Evidence: `openspec/specs/night-verdict/spec.md` (timeline hour requirements) |
| D6 | What does an hour no provider returned hold? | All eighteen keys, as today: the time and both altitudes, and null for every weather value and both cloud band keys. | Evidence: `openspec/specs/night-verdict/spec.md` (eighteen keys in a fixed order) |
| D7 | Does this keep the verdict contract? | Yes. No key is added or renamed. The timeline only gains entries, and the verdict, gates, score, confidence, reasons and every other field are unchanged: the document without `timeline` stays byte-identical. The timeline is never empty any more, so "empty, never absent" is replaced by "carries the night's astronomy when no provider returned rows". | Evidence: `AGENTS.md` (frozen verdict contract) |
| D8 | Does the MQTT adapter change? | No. The timeline sensors already publish one point per entry and a state from the current hour's entry, so during an outage Sun altitude and Moon altitude get a state, and the other sensors stay `unknown` with null points. The `ha-delivery` scenarios for an empty timeline describe the adapter and stay. | Evidence: `openspec/specs/ha-delivery/spec.md` |
| D9 | Does the card change? | No. The strip's reach counts every point whatever its value, so the altitude rows and the dusk and dawn shading fill the opening axis during an outage with no card change. | Evidence: `openspec/specs/night-card/spec.md` ("The reach counts every row's forecast") |
| D10 | Which goldens change? | The goldens in `tests/fixtures/golden/expected/` are regenerated: `empty.json` goes from 0 to 24 entries, and the others gain the hours from solar noon (11:58 UTC) that the recorded forecasts do not cover. The `stub` goldens the issue names leave the timeline out (`tests/test_producer_targets.py`), so they do not change. | Evidence: `tests/test_producer_targets.py`, `tests/fixtures/golden/expected/` |
| D11 | Which documents change? | The glossary's Timeline entry (committed on this branch), and `docs/night-timeline.md`: "What the timeline is" says how far the timeline reaches, and the paragraph saying the altitudes go `unknown` with no provider is replaced. ADR-0025 stands: its decision, a flat timeline as evidence beside the verdict, is unchanged, and the hour rule lives in the spec. | Assumption |
| D12 | Is the story the right size? | Yes: one core function, its spec, the goldens, the existing timeline tests that count entries, and one doc page. About eight tasks. | Assumption |

## Changes from the story

- The issue lists the `stub` golden verdict as changing. It leaves the timeline
  out, so the `expected` goldens change instead (D10).
- Added: the hours from the current hour to the solar day (D2) and a rule for a
  night with no dark window (D3), so the altitude sensors have a state at every
  instant during an outage, not only during the night.

The brief's instruction to proceed on recommendations stands in for the user's
confirmation of this ledger.

Confirmed by user: yes
