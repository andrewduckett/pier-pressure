## Story

#188 card-visual-editor — the card's pier is picked from a list in a visual
editor.
https://github.com/andrewduckett/pier-pressure/issues/188

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

The Verdict sensor's attributes hold every key of the verdict document except
`timeline`, so its `pier` attribute already holds the pier id. The editor can
list piers from published entities alone. Only the card and its docs change.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | `night-card` only. `ha-delivery` and `night-verdict` do not change: the Verdict sensor already carries the pier id | Evidence: `pierpressure/delivery/mqtt.py`, attributes are the document without `timeline`; `pierpressure/core/model.py`, `VerdictDocument.pier` |
| D3 | Where does "the piers Home Assistant knows" come from? | Home Assistant's states: each entity whose id has the form `sensor.pierpressure_<slug>_verdict` is one pier. Not the device or entity registry, since the card reads only published states | Evidence: #132 Shared decisions ("reads only published entities"); `card/src/pierpressure-card.ts`, `HomeAssistant` reads only `states` |
| D4 | What value does picking a pier set as `pier`? | The sensor's `pier` attribute when it slugs back to that sensor's id. Otherwise the `<slug>` part of the id: before the first verdict there is no attribute, and a pier id in another alphabet does not slug back. The editor never sets a value that misses the sensor it listed | Evidence: `docs/night-card.md`, "Find your pier's entity id" (use the part between `pierpressure_` and `_verdict`); `card/src/entity.ts` `pierSlug` |
| D5 | What does the list show, and in what order? | Each pier's `pier` attribute, or its slug when there is none, sorted alphabetically | Assumption |
| D6 | What if the configured pier is not in the list, such as one typed in YAML or one Home Assistant has lost? | The editor still shows it as the current pier and never replaces it on its own | Assumption |
| D7 | Can the user type a pier that is not listed? | Yes. The docs' fix for a renamed entity is a typed `pier`, and a pier may not have published yet | Evidence: `docs/night-card.md`, "Find your pier's entity id" |
| D8 | What if Home Assistant has no PierPressure Verdict sensor at all? | The editor says no PierPressure piers were found, and still lets the user type one | Assumption |
| D9 | Which options does the editor edit? | Only `pier`. Every other key in the card's configuration is kept as it was | Evidence: #188 Scope ("out: editing per-row options in the editor") |
| D10 | How does the card appear in the card picker? | Its picker entry asks for a preview, and the card offers a starting configuration with the first listed pier, so the preview draws that pier's real verdict | Evidence: #188 Scope ("the card appears in the card picker with a preview") |
| D11 | What starting configuration does the picker get when no pier is found? | One with no `pier`. The picker then shows the card's description in place of a preview; once the card is picked, the edit dialog's preview shows "pier is required", the card's existing error, and the editor says no piers were found | Assumption |
| D12 | Does the change need a glossary term? | No. "Pier" is the `id` in PierPressure's `piers` setting, as the docs already say, and the glossary has no pier term to clash with | Evidence: `openspec/glossary.md`; `docs/night-card.md`, "Add the card to a dashboard" |
| D13 | What do the docs say? | `docs/night-card.md`: "Add the card to a dashboard" picks the card from the picker and the pier from the editor's list, with YAML as the other route; "Find your pier's entity id" says the list already uses the real id | Evidence: #188 Scope |
| D14 | How does the agent see it working before merge? | In `mise run dashboard-check`'s real Home Assistant, by eye, on the editable Overview dashboard: the card is in the picker with a preview, and picking a pier in the editor changes the card. A second Verdict sensor set through the state API gives the list two piers | Evidence: `scripts/dashboard_check.py`; card-moon-drawing checked its drawing the same way |

## Changes from the story

None. The story stands as written. The editor also accepts a typed pier (D7),
so the list never makes a working YAML configuration impossible to keep.

Confirmed by user: yes
