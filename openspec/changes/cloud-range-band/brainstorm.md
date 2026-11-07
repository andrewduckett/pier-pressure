## Story

#186 cloud-range-band — two new sensors publish the lowest and highest forecast
cloud, and the card shades the band between them.
https://github.com/andrewduckett/pier-pressure/issues/186

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

The core already computes both values (#158): each timeline entry's
`cloud_cover_min` and `cloud_cover_max` are the lowest and highest cloud cover
any provider gave for the hour, and both are null when fewer than two did. Only
delivery and the card change.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | `ha-delivery` for the two sensors and `night-card` for the row and its docs. `night-verdict` does not change: the document already carries both keys | Evidence: `openspec/specs/night-verdict/spec.md`, the cloud band keys |
| D3 | What are the two sensors called? | Cloud cover min and Cloud cover max, keys `cloud_cover_min` and `cloud_cover_max`, unit `%`, the cloud icon, no device class, like every other timeline sensor. The name slugs to the key, as for the other fifteen | Evidence: `pierpressure/delivery/mqtt.py` `TIMELINE_SENSORS`; `tests/test_timeline_sensors.py`, name slugs to key |
| D4 | Where do they go in the sensor table? | Last, after Precipitation probability, so every message published before them keeps its place | Evidence: `TIMELINE_SENSORS` comment (timeline-sensors DD6); `TimelineEntry` puts the two keys last |
| D5 | What are their state and attributes? | The same as every further timeline sensor: the current hour's value, `unknown` when it is null, and a `forecast` list with one point per timeline hour. So an hour with fewer than two forecasts is `unknown` or a null point | Evidence: `ha-delivery` spec, the further timeline sensor requirements; ADR 0025 |
| D6 | Does the band change the Cloud cover row? | No. The band is its own row, **Cloud range**, directly under Cloud cover. The Cloud cover row keeps its shades, hover text and message. A 16 px shaded cell has no room for a second reading, and a row of its own has a place for its own message | Assumption |
| D7 | How does the Cloud range row draw an hour? | The row's height stands for 0 to 100% cloud, with 0 at the bottom. Each hour with both values has a shaded bar from the lowest to the highest value. A tall bar means the forecasts disagree; where the bar sits shows how cloudy they say it is | Assumption |
| D8 | What about an hour with one forecast, or a min with no max? | The hour stays blank. The card draws an hour only when both sensors give it a number | Evidence: #186 Scope ("absent for an hour with fewer than two forecasts"); `night-verdict` spec, both null together |
| D9 | What does hovering over an hour show? | `Cloud range, the hour from 21:00: 40% to 70%`, in the style of every other cell | Assumption |
| D10 | What does the row show when it draws no bar at all? | A message, the first that applies: `Not found` or `Unavailable` for the first of the two sensors (min, then max) that is missing or unavailable; otherwise `Needs two forecasts`. Hovering names the sensor for the first two, as other rows do, and says the row needs cloud cover from two or more forecasts for the same hour for the third | Assumption |
| D11 | Why not `No forecast` for the third case? | With the default providers only Open-Meteo gives cloud cover (7Timer! gives seeing and transparency), so the row is empty on most installs. `No forecast` would read as a fault; `Needs two forecasts` says what is missing, and the docs say how to add a second cloud provider | Evidence: README `providers` default; `pierpressure/conditions/seven_timer.py` |
| D12 | Is the row hidden when it has nothing to draw? | No. Every row stays, so the strip's layout never moves with the forecast, and the message tells an adopter the row exists | Assumption |
| D13 | Is the row called an "agreement band"? | No. The glossary's Agreement is measured over the night window and expressed as a band for confidence; this row is per hour and is not that measure. The card and docs say "Cloud range" and "lowest and highest cloud cover any forecast gives" | Evidence: `openspec/glossary.md`, "Agreement" |
| D14 | Does the change need a glossary term? | No. "Cloud range" is a row label, like "Rain chance", and "Night strip" already covers rows | Evidence: `openspec/glossary.md`, "Night strip" |
| D15 | What do the docs say? | `docs/night-timeline.md`: the two sensors in the sensor table and the recorder exclusions, and "seventeen sensors". README: the entity table and the MQTT topic tables. `docs/night-card.md`: the row, how to read it, its hover, its message, and what to do about `Needs two forecasts` | Evidence: #186 Scope |
| D16 | Does the YAML dashboard draw the band? | No | Evidence: #186 Scope ("out: the YAML dashboard") |
| D17 | Do agreement or confidence change? | No | Evidence: #186 Scope ("out: any change to how agreement is measured or to confidence") |
| D18 | How does the agent see it working before merge? | In `mise run dashboard-check`'s real Home Assistant, the agent checks by eye that both sensors appear and the Cloud range row draws bars, or says `Needs two forecasts` when the pier has one cloud provider | Evidence: `scripts/dashboard_check.py`; the card-unavailable-states change did the same |

## Changes from the story

None. The story stands as written. The band is drawn beside the Cloud cover
row, as a row of its own, which the story allows ("on or beside").

Confirmed by user: yes
