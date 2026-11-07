## Story

#185 card-unavailable-states — the card says what is missing when PierPressure
is offline or a sensor has no forecast.
https://github.com/andrewduckett/pier-pressure/issues/185

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

Two of the story's four cases are already built by the walking skeleton
(#180): the offline message and the message for a pier with no Verdict sensor.
This change keeps both, and adds the other two and the docs.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | Only `night-card`. The requirements that leave a row or the Moon up lane empty change to say what the row shows instead; new requirements cover the darkness note and the troubleshooting docs | Assumption |
| D3 | What does the card show when PierPressure is offline? | No change: "PierPressure is offline" in place of the verdict and the strip. All of a pier's entities share one availability topic, so they go unavailable together, and Home Assistant hides their attributes | Evidence: `night-card` spec, "An unavailable Verdict sensor says PierPressure is offline"; `pierpressure/delivery/mqtt.py` `availability_topic` |
| D4 | What does the card show when `pier:` names no PierPressure pier? | No change: "No PierPressure verdict found: <entity id>", with no verdict and no strip | Evidence: `night-card` spec, "A missing Verdict sensor is named" |
| D5 | When does a row say what is missing? | When it would draw no cell at all. A row with some cells keeps its blank hours blank, as now | Assumption |
| D6 | What does such a row say? | By cause: "Not found" when Home Assistant has no such entity; "Unavailable" when its state is `unavailable`; "No forecast" otherwise (no `forecast` list, an empty one, or no value on the axis) | Assumption |
| D7 | Where and how does a row show it? | As text in the row's track, in the secondary text colour at the time labels' size. Hovering over it names the entity id and the cause, so the user can find the sensor | Assumption |
| D8 | Does the Moon up lane say what is missing? | Yes, the same words as the Moon altitude row, because it reads the same sensor. A forecast with the moon down all night shows no bar and no message, as now | Assumption |
| D9 | Do the target lanes change? | No: a rank with no target tonight leaves no lane, whatever the cause | Evidence: `night-card` spec, "A rank with no target tonight leaves no lane" |
| D10 | What does the card show when `dark_window` is null? | A note "No astronomical darkness tonight" between the verdict lines and the strip, when `dark_window` has a null `start` and a null `end`. The strip still draws on its fallback axis, as now | Evidence: README, `dark_window` is null when there is no astronomical darkness; placement is an Assumption |
| D11 | Does a missing or unreadable `dark_window` show that note? | No. Before the first verdict there is no `dark_window`, and the dashes already say so; a malformed window is a hand-edited state. Both keep the fallback axis with no note | Assumption |
| D12 | Does the verdict's `unknown` state change? | No: dashes, as now. Its rows will say "No forecast", which is true before the first verdict | Assumption |
| D13 | What do the docs say? | `docs/night-card.md` lists the row messages and the darkness note where it describes the strip, and its "If something looks wrong" section covers offline, no verdict found, a row that says Not found, Unavailable or No forecast, and the darkness note | Evidence: #185 Scope |
| D14 | Is a version attribute for detecting the document's shape in scope? | No | Evidence: #185 Scope ("out: a version attribute"); #132 Shared decisions (release pairing) |
| D15 | Does the change need a glossary term? | No: "Night strip" covers rows and lanes, and the messages are display text, not domain terms | Evidence: `openspec/glossary.md`, "Night strip" |
| D16 | How is it seen working before merge? | `mise run dashboard-check` shows the locally built card in a real Home Assistant; stopping PierPressure there shows the offline message, checked by eye | Evidence: `scripts/dashboard_check.py` |

## Changes from the story

None. The story stands as written. The offline and no-verdict messages it lists
already exist; this change keeps them and documents them.

Confirmed by user: yes
