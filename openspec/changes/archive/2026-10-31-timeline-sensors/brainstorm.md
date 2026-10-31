## Story

#134 timeline-sensors — every timeline variable is a sensor with a forecast array
https://github.com/andrewduckett/pier-pressure/issues/134

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which variables get a sensor? | The eight timeline keys without one: `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `sun_altitude`, `moon_altitude`. No new variables. | Evidence: issue #134 Scope; `TimelineEntry` in `pierpressure/core/model.py` |
| D2 | How does each sensor behave? | Exactly like Cloud cover: retained discovery on the pier's device, enabled by default, available exactly when the process is online, no `state_class`; state is the current hour's value or `None`; attributes are exactly `hour` and `forecast`. | Evidence: issue #134 Scope; `openspec/specs/ha-delivery/spec.md` Cloud cover requirements |
| D3 | Is `hour` and the `None` state judged per variable? | Yes. Each sensor's state and `hour` come from its own variable's value in the current hour, so Seeing can be unknown while Cloud low has a value. | Evidence: ha-delivery spec, "`hour` SHALL be the `time` of the entry the state comes from" |
| D4 | What are the sensors called? | Names match the timeline keys: Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency, Sun altitude, Moon altitude, so each entity id ends in its key (`sensor.pierpressure_<pier>_cloud_low`). | User |
| D5 | What scale do Seeing and Transparency publish? | 0 to 1, exactly as the timeline holds them, with no unit. | User |
| D6 | Unit and device class for Wind gust? | km/h, no device class, so Home Assistant never converts the state away from the forecast array's unit. | User |
| D7 | Units for the other sensors? | `%` for the three cloud layers, `°` for the sun and moon altitudes, no device class on any. | Assumption |
| D8 | What do the altitude sensors' states mean? | The altitude at the start of the current hour, as the timeline holds it, not the live altitude. The docs say so. | Assumption |
| D9 | What happens to Cloud cover and the other entities? | Unchanged: topics, payloads and unique identities stay as they are. | Evidence: AGENTS.md frozen delivery surface; ha-delivery spec |
| D10 | What documentation changes? | A README entity row and topic row for the new sensors; `docs/night-timeline.md` describes every sensor and its recorder exclusion list names all nine forecast sensors. | Evidence: issue #134 Scope; `docs/night-timeline.md` already holds the Cloud cover recorder note |
| D11 | How is it accepted? | Each discovery payload validates against `SENSOR_SCHEMA`; each sensor's attributes mirror its timeline key hour for hour and stay under 16 KiB at 120 hours; a null current hour publishes `None`. | Evidence: ha-delivery spec Cloud cover scenarios |

## Changes from the story

None. The recorder note the story asks for already exists for Cloud cover
(from #133), so this story extends it to the new sensors rather than writing it.

Confirmed by user: yes
