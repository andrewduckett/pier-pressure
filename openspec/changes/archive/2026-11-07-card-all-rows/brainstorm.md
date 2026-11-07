## Story

#183 card-all-rows — seeing, transparency, wind, temperature, dew point,
humidity and rain chance join the card's strip.
https://github.com/andrewduckett/pier-pressure/issues/183

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | Only `night-card`: the new rows, their shades and the docs get new requirements, beside the cloud and Sun altitude rows' own; the null-hour rule and the lane and line requirements widen to every row. `night-dashboard` is the reference, not changed | Assumption |
| D3 | Which rows join the strip? | One per timeline sensor the strip lacks: Moon altitude, Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind speed, Wind direction and Rain chance. The Moon up lane stays below the rows | Evidence: #183 Scope; `pierpressure/delivery/mqtt.py` `TIMELINE_SENSORS` |
| D4 | In what order, top to bottom? | The YAML strip's nine in its order (Sun altitude, Moon altitude, the four cloud rows, Wind gust, Seeing, Transparency), then the rest in `TIMELINE_SENSORS` order: Temperature, Dew point, Humidity, Wind speed, Wind direction, Rain chance. Moon altitude moves in between Sun altitude and Cloud cover, so the cloud rows are no longer right under the Sun altitude row | Evidence: `docs/night-dashboard.md` `categoryarray`; `TIMELINE_SENSORS` |
| D5 | What is the Precipitation probability row called? | Rain chance: the issue's own word, and short enough that the label column does not squeeze the strip on a phone; the docs say it covers rain or snow | Assumption |
| D6 | Which hour does a Rain chance value fill? | The hour that ends at its `datetime`, not the one that starts there, because the timeline holds the chance for the hour before `time`. Its hover names the start of the hour it fills, like every other row | Evidence: `docs/night-timeline.md` `precipitation_probability` |
| D7 | How are the YAML strip's rows shaded? | As in the YAML strip, in the same seven blues: Moon altitude step 0 at 0° or below, else `min(6, 1 + floor(v / 6))`; Wind gust `min(6, floor(v / 7))`; Seeing and Transparency `min(6, round((1 − q) × 7))`, so darker is worse. Every step is held between 0 and 6 | Evidence: `docs/night-dashboard.md` YAML `rows` |
| D8 | How are Temperature and Dew point shaded? | One shared scale, so the two rows can be compared by eye: seven steps of 5 °C, `min(6, max(0, floor((v + 10) / 5)))`, from lightest below −5 °C to darkest at 20 °C or more. Darker is warmer, keeping the strip's rule that darker means more of what the row names | Assumption |
| D9 | How are Humidity, Wind speed and Rain chance shaded? | Humidity and Rain chance like cloud, one step per 15%; Wind speed like Wind gust, one step per 7 km/h, so the two wind rows compare | Assumption |
| D10 | How does Wind direction read as a direction? | Each hour holds an arrow and no shade. The arrow points the way the wind blows to, the reverse of the `from` direction the sensor holds, as on a weather map. A null hour has no arrow | Assumption |
| D11 | What does hovering over a cell show? | `<row>, the hour from <HH:MM>: <value><unit>` with the value as the forecast holds it and the sensor's unit: `°`, `%`, ` km/h`, ` °C`, or none for Seeing and Transparency. Wind direction adds an 8-point compass name: `225° from SW` | Evidence: #183 Scope ("the unit on hover"); `TIMELINE_SENSORS` units |
| D12 | Does the card convert units, such as km/h to mph? | No. The `forecast` attribute is always km/h and °C, and Home Assistant does not convert attributes | Evidence: `pierpressure/delivery/mqtt.py` units; `docs/night-timeline.md` |
| D13 | What if a new row's sensor is missing, unavailable or has a null hour? | The same as a cloud row: the row keeps its label, a null hour is blank, and the card never throws | Evidence: #132 Shared decisions; `night-card` spec, missing cloud sensor |
| D14 | Do the lines cross the new rows? | Yes: dusk, dawn and now reach from the top row to the Moon up lane, as now | Evidence: `night-card` spec, the three lines |
| D15 | Does the card get an option to choose which rows show? | No. The packet leaves it out, and the visual editor story (#188) is where a row picker would sit; all fifteen rows show | Evidence: #183 Scope ("out: choosing which rows show") |
| D16 | Does the change need a glossary term? | No: "Night strip" already means one row per condition | Evidence: `openspec/glossary.md`, "Night strip" |
| D17 | What do the docs say? | `docs/night-card.md` lists all fifteen rows and their sensors, gives each row's lightest and darkest, says Rain chance fills the hour before its time and how the wind arrows point, and its opening no longer says other conditions come later | Evidence: #183 Scope |
| D18 | How is it seen working before merge? | `mise run dashboard-check` shows the locally built card beside the YAML strip in a real Home Assistant, checked by eye | Evidence: `scripts/dashboard_check.py` |

## Changes from the story

None. The dew-risk mark and a row picker stay out, as the packet says.

Confirmed by user: yes
