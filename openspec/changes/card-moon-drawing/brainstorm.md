## Story

#187 card-moon-drawing — the card draws the moon at tonight's phase and
illumination.
https://github.com/andrewduckett/pier-pressure/issues/187

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

The Verdict sensor's attributes are the whole verdict document, so its `moon`
attribute already holds `illumination` (0 to 1, two decimals), `phase` (one of
eight names), and `rise` and `set` (inside the dark window, or null). Only the
card and its docs change.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | `night-card` only. `night-verdict` and `ha-delivery` do not change: no new field and no new sensor | Evidence: #187 Scope ("out: any new field in the document") |
| D3 | What does the card read? | The Verdict sensor's `moon` attribute: `illumination`, `phase`, `rise` and `set`. Nothing else from PierPressure | Evidence: README, `moon` field; `pierpressure/delivery/mqtt.py`, the Verdict sensor's `json_attributes_topic` |
| D4 | What does the card show? | A moon drawing, and beside it the phase name, the illumination as a percent, moonrise and moonset. The same four facts as the YAML dashboard's Moon card | Evidence: `docs/night-dashboard.md`, Moon card; #187 Scope |
| D5 | Where does it go? | Beside the Verdict, Score and Confidence lines, above the strip. It is part of tonight's summary, not of the hour-by-hour strip | Assumption |
| D6 | How does the drawing show illumination? | A disc whose lit part is the illumination's share of the disc, with the usual curved terminator. No position angle, libration or earthshine | Evidence: #187 Scope ("out: libration or exact terminator geometry") |
| D7 | Which side is lit? | Waxing phases are lit on the right, waning on the left, as seen from the northern hemisphere. Mirrored when Home Assistant's latitude is south of the equator, since the card already reads Home Assistant's time zone the same way | Assumption |
| D8 | What do `new` and `full` draw? | `new` an unlit disc, `full` a fully lit disc, whatever the illumination. The document does not say which side a sliver is on in those two phases, and the sliver is at most 4% of the disc | Evidence: `pierpressure/core/sky.py`, the 45° phase octants |
| D9 | How is the illumination written? | A whole percent, such as `78%`, as the YAML Moon card rounds it | Evidence: `docs/night-dashboard.md`, Moon card template |
| D10 | How is the phase written? | The document's name with a capital first letter, such as `Waxing gibbous`, like the card's other labels | Assumption |
| D11 | How are moonrise and moonset written? | Times in Home Assistant's time zone on a 24-hour clock, as on the strip. A dash when the value is null: the moon does not rise or set inside the dark window, or there is no dark window | Evidence: README, `moon.rise` and `moon.set`; `card/src/strip.ts` `clock` |
| D12 | Does the card use `up_during_dark`? | No. The Moon up lane already shows when the moon is up | Evidence: `docs/night-card.md`, Moon up lane |
| D13 | What if `moon` is missing or malformed, such as before the first verdict or from an older PierPressure? | Each text shows a dash when its own value is missing or invalid, like the Verdict lines. The drawing shows only when both `illumination` and `phase` are valid. An empty outline would read as a new moon | Assumption |
| D14 | What does hovering or a screen reader get? | The drawing has a text alternative, such as `Moon: waxing gibbous, 78% lit` | Assumption |
| D15 | What happens when PierPressure is offline or the Verdict sensor is not found? | No moon. The card shows only its message, as it already does for the strip | Evidence: `card/src/pierpressure-card.ts` `renderBody` |
| D16 | Does the change need a glossary term? | No. "Moon" is a card label, and the glossary has no moon term to clash with | Evidence: `openspec/glossary.md` |
| D17 | What do the docs say? | `docs/night-card.md`: the moon's lines in "What the card shows", how to read the drawing, which side is lit and why, and what a dash means. The YAML dashboard and its docs do not change | Evidence: #187 Scope |
| D18 | How does the agent see it working before merge? | In `mise run dashboard-check`'s real Home Assistant, the agent checks by eye. It sets the Verdict sensor's state with a few `moon` attributes through Home Assistant's state API, and sees each phase drawn | Evidence: `scripts/dashboard_check.py`; the cloud-range-band change set states the same way |

## Changes from the story

None. The story stands as written. The card also shows the phase name and the
illumination as text beside the drawing, as the YAML Moon card does; both are
`moon` fields the story already names.

Confirmed by user: yes
