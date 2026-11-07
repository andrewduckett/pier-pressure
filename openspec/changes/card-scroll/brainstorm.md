## Story

#189 card-scroll — the card's strip drags sideways through every forecast
hour.
https://github.com/andrewduckett/pier-pressure/issues/189

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

Today the strip's axis is fixed: from 4 hours before dusk to 5 hours after
dawn, or from 6 hours before now to 18 hours after on a night with no
astronomical darkness. The timeline sensors already carry every hour the
timeline holds, usually two to three days, and the card drops the hours off the
axis. So panning needs no new data. Only the card and its docs change.

In this ledger, the **axis** is the span of time the strip shows, as today.
The **opening axis** is today's fixed axis, and the **reach** is how far the
axis can pan.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | `night-card` only. The core, the published entities and the YAML strip (#173) do not change | Evidence: #189 Scope |
| D3 | What does the strip open on? | The opening axis, the same axis as today: the judged night with 4 hours before dusk and 5 after dawn, or the day around now when there is no dark window | Evidence: #189 Scope ("the strip still opens on the judged night"); `night-card` spec, "The strip spans the judged night" |
| D4 | How long is the axis while it pans? | Always as long as the opening axis. Panning moves the axis along the timeline; it never zooms | Evidence: #189 outcome ("drag it sideways"); #173 Why (the YAML strip's box-zoom drag is what makes other hours awkward to reach) |
| D5 | How far can the axis pan? | Across every hour the timeline holds, and never less than the opening axis. The axis stops at those ends | Evidence: #189 outcome ("every hour the timeline holds"); `openspec/glossary.md`, "Timeline" |
| D6 | Which inputs pan the axis? | A mouse drag, a touch swipe, a trackpad's sideways swipe, and the Left and Right arrow keys while the strip has focus. An up or down swipe still scrolls the page | Assumption: the keys serve anyone who cannot drag; a phone user must still be able to scroll past the card |
| D7 | What moves with the axis? | Every row, the Cloud range row, the Moon up lane, every target lane, the dusk, dawn and now lines with their labels, and the time labels. The row labels stay where they are | Evidence: #189 Scope ("every row, lane and line moves together") |
| D8 | What does the strip show on a night other than the judged one? | Its rows and Moon up bars, and no dusk line, dawn line or target bar: the Verdict sensor carries one dark window and the Target sensors one night's windows. The Sun altitude row still shows that night's darkness. Each line shows only while its time is on the axis | Evidence: `card/src/strip.ts`, `darkWindow` and `targetLanes`; the Verdict sensor's `dark_window` |
| D9 | How are cells, bars and hover texts drawn at the axis ends? | As at today's axis ends: a cell or bar is cut off at the axis end, and its hover text is unchanged | Evidence: `night-card` spec, "A value fills its hour" and "A target bar spans its window" |
| D10 | Which time labels does the axis carry? | Today's rule, applied to the panned axis: every 3 hours, or every 6 when the axis is longer than 24 hours | Evidence: `night-card` spec, "The axis carries time labels" |
| D11 | What happens to the axis when Home Assistant sends new state, or the card redraws each minute? | Until the user pans, the axis is the opening axis, so it follows the clock on a night with no darkness and moves to a new judged night. Once the user has panned, the axis keeps its start, held inside the reach. A pan the reach stops entirely counts as no pan | Assumption: a redraw that jumped the axis back would undo the user's drag every minute |
| D12 | How does the user get back to the judged night? | A "Back to tonight" button shows above the strip while the axis is off the opening axis. Selecting it returns the axis there. Reloading the page also opens on the opening axis | Assumption: dragging back across three days is slow on a phone, and the YAML strip's double-click reset has no touch equivalent |
| D13 | Does the change need a glossary term? | No. Opening axis and reach are named only in the `night-card` spec, beside the strip's axis, which the spec already names. The glossary's "Night strip" already covers the strip | Evidence: `openspec/glossary.md`, "Night strip" |
| D14 | What do the docs say? | `docs/night-card.md`: the strip opens on the judged night; how to pan with a mouse, a finger, a trackpad and the keys; that the axis stops at the first and last forecast hour; that other nights have no dusk, dawn or target bars; that a row says "No forecast" past its weather source's last hour; and the "Back to tonight" button | Evidence: #189 Scope ("`docs/night-card.md` updated") |
| D15 | How does the agent see it working before merge? | In `mise run dashboard-check`'s real Home Assistant, by eye: drag the strip, pan with the keys, and select "Back to tonight". card-visual-editor checked its editor the same way | Evidence: `scripts/dashboard_check.py`; `openspec/changes/archive/2026-11-07-card-visual-editor/brainstorm.md`, D14 |
| D16 | What if a touch meant to scroll the page, or to tap a cell, moves a few pixels sideways? | It pans nothing. A drag starts only once the pointer has moved clearly sideways, and a gesture the browser takes over for scrolling leaves the axis where it was | Assumption: a phone browser sends a few sideways pointer moves before it takes a vertical swipe for scrolling, and a tap rarely lands still |

## Changes from the story

Added: the "Back to tonight" button (D12) and the arrow keys (D6). The story
asks only for a drag or swipe. Without the button, returning from the last
forecast night takes as many drags as leaving it; without the keys, a user who
cannot drag cannot pan at all.

Confirmed by user: yes
