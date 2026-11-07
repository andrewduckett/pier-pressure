## Story

#184 card-target-windows — each ranked target's window is a lane on the card's
time axis.
https://github.com/andrewduckett/pier-pressure/issues/184

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | Only `night-card`: new requirements for the target lanes and their docs, and the dusk, dawn and now lines widen to cross the lanes. `night-dashboard` is the reference, not changed | Assumption |
| D3 | Which sensors does a lane read? | `sensor.pierpressure_<slug>_target_1` to `_target_10`, named from the same slug as the Verdict sensor. The lane's name is the sensor's state, the target's display name; its window is the `window` attribute's `start` and `end` | Evidence: `pierpressure/delivery/mqtt.py` `rank_target_state`, `rank_target_attributes` |
| D4 | When does a rank get a lane? | When its sensor exists, is not `unavailable`, and its `window` has a `start` and `end` that parse, with `end` after `start`. Anything else leaves no lane and never throws. An empty rank is unavailable, so it leaves no lane | Evidence: #184 Scope; #132 Shared decisions (tolerate a missing sensor or attribute); `night-dashboard` spec, one lane per ranked target |
| D5 | Where do the lanes sit, and in what order? | Under the Moon up lane, one per rank in rank order, Target 1 first. A rank with no lane leaves no gap | Evidence: `night-dashboard` spec, one lane per ranked target |
| D6 | What labels a lane, and what labels its bar? | The label column reads `Target <n>`, as the YAML strip's lanes do. The bar holds the target's name, from its left end, cut short with an ellipsis when the bar is too narrow | Evidence: `docs/night-dashboard.md` YAML `pier_targets` and `Lanes` trace |
| D7 | What does a bar look like? | Violet `#6250d6` with white text and 4 px rounded corners, as in the YAML strip, so a target never looks like the grey Moon up bar | Evidence: `docs/night-dashboard.md` YAML `Lanes` marker colour |
| D8 | What if a window runs past an axis end? | The bar is cut off at the axis end, as a Moon up bar is. A window wholly off the axis keeps its lane with no bar. The core clamps a window to the dark window, so this happens only with a stale or hand-edited state | Evidence: `night-card` spec, Moon up bar cut off at the axis; `docs/target-ranking.md` |
| D9 | What does hovering over a bar show? | `<name> from <HH:MM> to <HH:MM>`: the window's own start and end, even where the axis cuts the bar off, in Home Assistant's time zone, like a Moon up bar | Assumption |
| D10 | Do the dusk, dawn and now lines cross the target lanes? | Yes: they reach from the top row to the last lane, so a window reads against dusk, dawn and now | Assumption |
| D11 | Does the card's size grow with the lanes? | Yes: `getCardSize` adds to its fixed 10 for the lanes shown, so a dashboard leaves room for up to ten more lanes without reserving it on a night with none | Assumption |
| D12 | Does the lane show more than the name and window? | No: score, altitude, transit and the other target fields stay out, and the card picks no targets | Evidence: #184 Scope ("out: target details beyond name and window; picking targets in the card") |
| D13 | Does the change need a glossary term? | No: "Night strip" already covers lanes on the time axis, and "observable window" is defined by `target-ranking` | Evidence: `openspec/glossary.md`, "Night strip"; `target-ranking` spec |
| D14 | What do the docs say? | `docs/night-card.md` describes the target lanes: which sensors, the label, the bar, the hover text, and that a rank with no target tonight leaves no lane. Its opening names the targets beside the conditions | Evidence: #184 Scope |
| D15 | How is it seen working before merge? | `mise run dashboard-check` shows the locally built card beside the YAML strip in a real Home Assistant, checked by eye | Evidence: `scripts/dashboard_check.py` |

## Changes from the story

None. The story stands as written.

Confirmed by user: yes
