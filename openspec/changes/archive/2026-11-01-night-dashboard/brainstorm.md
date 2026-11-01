## Story

#135 night-dashboard — a documented dashboard shows the night strip with dusk, dawn, moon and targets.
https://github.com/andrewduckett/pier-pressure/issues/135

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Where does the check against a real Home Assistant run? | A throwaway Home Assistant in Docker, with mosquitto and PierPressure, and plotly-graph-card installed by hand. It never touches Andrew's Home Assistant. | User |
| D2 | What time span does the strip show? | Tonight with margins: a few hours before dusk to a few hours after dawn, from the Verdict's `dark_window`. When `dark_window` is null, a fixed span around now. | User |
| D3 | How does the moon-up span appear? | A "Moon up" bar on its own lane, drawn like a target span, covering the hours where the Moon altitude forecast is above 0°. | User |
| D4 | How many target spans does the strip draw? | Every ranked target, one lane per rank, labelled by name. An empty rank leaves no lane. | User |
| D5 | What guards the YAML once it ships? | A pytest test parses the dashboard YAML from the docs page and checks that every PierPressure entity id and attribute it reads is one the MQTT adapter publishes. | User |
| D6 | Is there a screenshot, and where does it live? | Yes, one taken during the Docker check, in `docs/images/` on main. | User |
| D7 | Where does the "now" line come from? | The browser's current time, not `generated_at`. | User |
| D8 | Which rows, and how are they shaded? | The nine rows in the packet's order. A null hour is a gap. Darker means more of what the row names, or poorer for Seeing and Transparency. The Sun row darkens as the sky darkens, and the Moon row as the moon climbs. | Evidence: `night-strip-mock.html` on the `assets` branch; #135 Scope |
| D9 | Which time zone does the axis use? | Home Assistant's local time, not UTC. | Assumption |
| D10 | Where does the page live? | A new `docs/night-dashboard.md`, linked from the README's entity section and from `docs/night-timeline.md`. The apexcharts-card example stays as it is. | Assumption |
| D11 | Which pier does the YAML name? | `backyard`, like the other docs, with a note to replace it. | Evidence: `docs/night-timeline.md` |
| D12 | What feeds the tonight card, moon card, target table and health chips? | Home Assistant core cards reading existing entities: the Verdict's attributes (`verdict`, `score`, `confidence`, `dark_window`, `reasons`, `moon`), Target 1 to 10, and the two health sensors. | Evidence: `README.md` entity table; #135 Scope |

## Changes from the story

None. The story stands as written. D7 settles a point that the thread's mock left open: the "now" line uses the live clock, not `generated_at`.

Confirmed by user: yes
