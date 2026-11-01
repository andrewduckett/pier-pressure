## Story

#136 timeline-weather-variables — temperature, dew point, humidity, wind and rain chance join the timeline
https://github.com/andrewduckett/pier-pressure/issues/136

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Do the six new sensors carry a device class? | No. They follow the #134 rule: no device class, so the state and the `forecast` attribute share one unit. | User |
| D2 | What are the document keys and sensor names? | `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`; named Temperature, Dew point, Humidity, Wind speed, Wind direction, Precipitation probability. | User |
| D3 | What units? | °C, °C, %, km/h, °, %: Open-Meteo's defaults, with the km/h wind unit the request already sets. | Evidence: `pierpressure/conditions/open_meteo.py` |
| D4 | Are values rounded? | No. They pass through as the base source reports them, like cloud cover and wind gust. | Evidence: `openspec/specs/night-verdict/spec.md`, "Cloud and wind values pass through unchanged" |
| D5 | Which source, and how do gaps behave? | All six come from the base source. Each is independently optional per hour on `SourceReading`, `BaseHour` and the timeline entry; a missing one is null, never an error. | Evidence: `openspec/specs/conditions/spec.md`, "Availability is stamped per field" |
| D6 | Where do the new entry keys go? | Appended after `transparency`, so every existing key keeps its position. | Evidence: `docs/decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md` and the night-verdict "fixed flat shape" requirement |
| D7 | How are the sensors delivered? | Six new rows in the timeline sensor table after Moon altitude: forecast array, current-hour state, unknown when null, available while online. | Evidence: `pierpressure/delivery/mqtt.py` `TIMELINE_SENSORS`, `openspec/specs/ha-delivery/spec.md` |
| D8 | What stays out? | Any gate or score term using these values (#98), and the dashboard rows. | Evidence: issue #136 scope |
| D9 | Does the golden verdict fixture change? | Yes, regenerated once, since the document grows additively. | Evidence: `tests/test_golden_verdict.py` docstring |

## Changes from the story

- Cut: "device classes" from the **Scope** line "with units and device classes". The sensors carry units only (D1), as the #134 spec rule requires.

Confirmed by user: yes
