## Story

#181 card-cloud-strip — the card draws the four cloud rows across the judged
night.
https://github.com/andrewduckett/pier-pressure/issues/181

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | Only `night-card`: added requirements for the strip and for its docs. `night-dashboard` is the reference, not changed | Assumption |
| D3 | Where does the strip go, and when does it show? | Below the verdict, score and confidence, inside the same card; only when those show, so a missing or unavailable Verdict sensor still shows just its message | Assumption |
| D4 | What does the time axis span? | From 4 hours before `dark_window.start` to 5 hours after `dark_window.end`; when either is null, from 6 hours before the browser's current time to 18 hours after it — the YAML strip's rule | Evidence: `night-dashboard` spec, "The strip spans tonight" |
| D5 | Which entities and rows? | `sensor.pierpressure_<slug>_cloud_cover`, `_cloud_low`, `_cloud_mid`, `_cloud_high`, top to bottom, labelled Cloud cover, Cloud low, Cloud mid, Cloud high; the slug is the Verdict sensor's | Evidence: `docs/night-timeline.md`, `night-dashboard` spec row order |
| D6 | How is a cell shaded? | The YAML strip's seven blues, `#cde2fb` lightest to `#0d366b` darkest, shade step `min(6, floor(value / 15))`, so more cloud is darker | Evidence: `docs/night-dashboard.md` YAML `ramp(v, 15)` |
| D7 | Which hour does a value cover, and which cells are drawn? | A point covers the hour that starts at its `datetime`; every hour that overlaps the axis is drawn, cut off at the axis ends; cells are rounded with a small gap, like the YAML strip | Evidence: `docs/night-dashboard.md` YAML; `night-dashboard` spec, rounded cells |
| D8 | What does missing data look like? | A null value, or an hour the forecast lacks, is a blank hour. A cloud sensor that is missing, unavailable or has no `forecast` leaves its row labelled and empty, and the card never throws | Evidence: #181 Scope; #132 Shared decisions ("the card tolerates a missing sensor or attribute") |
| D9 | What does hovering over a cell show? | The row, the hour's start time and the value with `%`, as the YAML strip's hover does: "Cloud cover, the hour from 21:00: 40%" | Evidence: `docs/night-dashboard.md` YAML `hovertemplate` |
| D10 | Which time zone, and which clock format? | Home Assistant's configured time zone, `hass.config.time_zone`, not the user profile's choice; a fixed 24-hour `HH:MM`, so every viewer reads the same times | Evidence: #181 Scope for the zone; Assumption for the 24-hour clock |
| D11 | Does the axis carry time labels? | Yes: a label at each whole hour in that time zone that is a multiple of 3, such as `18:00`, `21:00`, `00:00`, or of 6 when the axis spans more than 24 hours, so labels stay apart on a narrow card | Assumption |
| D12 | When does the strip redraw? | Whenever Home Assistant updates the card's state; no timer of its own, since the "now" mark that would need one is out of scope | Assumption |
| D13 | Does the change need a glossary term? | No: "night strip" already means a dashboard rendering of the timeline, and the card's strip is one | Evidence: `openspec/glossary.md`, "Night strip" |
| D14 | What do the docs say? | `docs/night-card.md` gains a section on the cloud rows: the axis span and its fallback, the shades, blank hours, hover and the time zone | Evidence: #181 Scope |
| D15 | How is the strip seen working before merge? | `mise run dashboard-check` already shows the locally built card against a live PierPressure, beside the YAML strip, so the two are compared by eye | Evidence: `scripts/dashboard_check.py` |

## Changes from the story

None.

Confirmed by user: yes
