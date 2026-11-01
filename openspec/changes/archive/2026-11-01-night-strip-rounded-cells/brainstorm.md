**Why:** The night strip's cells and lane bars are square because the strip is a heatmap, which renders as one raster image; redrawing each hour as a bar gives the rounded cells of the reference rendering now that the strip's data and layout are settled.

## Story

#143 night-strip-rounded-cells — the night strip's cells and lane bars have rounded corners like the reference rendering, https://github.com/andrewduckett/pier-pressure/issues/143

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What changes? | Only the `custom:plotly-graph` card in `docs/night-dashboard.md`, its prose, its screenshot and the doc tests. No entity, ADR or core change. | Evidence: #143 packet |
| D2 | How are the cells drawn? | One horizontal bar trace on the `y` axis with one bar per hour per row: `y` the row label, `base` the hour start plus the trim, `x` the hour length minus twice the trim, per-point `marker.color` from the same seven blues, `marker.cornerradius: 2`. One trace rather than nine. | Evidence: #143 packet |
| D3 | Corner radii? | 2 px for cells, 4 px for lane bars, as the mock's CSS sets them. | Evidence: `night-strip-mock.html` on the `assets` branch |
| D4 | Gap between cells along the hour? | Trim 2 minutes off each end of every hour bar. | Assumption |
| D5 | Gap between rows? | The rows trace sets `width: 0.85` of a row, so rows keep a gap like the mock's instead of inheriting the lanes' `bargap: 0.25`. | Assumption |
| D6 | A null hour? | No bar at all for that hour: the gap stays empty and hover does not fire there. `hoverongaps` goes away with the heatmap. | Evidence: night-dashboard spec, "A null hour is a gap" |
| D7 | Hover? | Unchanged text: the row, then "the hour from HH:MM: value", carried on each bar's `text`. | Evidence: #143 packet |
| D8 | Bar mode? | `barmode: overlay`, so bars at the same row with different bases are not grouped side by side. | Evidence: #143 packet |
| D9 | The six tests that assert a heatmap trace and exactly one bar trace? | Rewritten to assert the new shape: a rows bar trace with `marker.cornerradius: 2`, a lanes trace with 4, the ramp colours, the per-hour base and trim, and the null filter. The rest of the file is untouched. | Evidence: `tests/test_night_dashboard_doc.py` |
| D10 | Spec? | One ADDED requirement on `night-dashboard`: cells and lane bars have rounded corners, the radius checked in the YAML by the test and the rendering by the Docker check. | Assumption |
| D11 | Who checks it in a real Home Assistant? | The agent runs `mise run dashboard-check`, confirms the corners and hover in the browser, and refreshes `docs/images/night-dashboard.png`. The user sees the screenshot in the pull request. | User |
| D12 | The "Versions it was checked with" line? | Stays as is unless the check runs on other versions than Home Assistant 2026.10.4 and Plotly Graph Card v4.0.2. | Evidence: `docs/night-dashboard.md`, `compose.yaml` |
| D13 | ADR-0026? | Unchanged. Its decision is the card, not the trace type. | Evidence: #143 packet |

## Changes from the story

None. The packet's "tests stay green" is read as the tests passing after the heatmap assertions are rewritten for bars (D9), since six of them name the heatmap trace.

Confirmed by user: yes
