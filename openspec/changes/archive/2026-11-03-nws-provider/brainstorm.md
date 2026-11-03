## Story

#155 nws-provider — a pier can add the National Weather Service to its provider list, https://github.com/andrewduckett/pier-pressure/issues/155

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | NWS gives total cloud only. When `nws` is listed before an Open-Meteo provider, what happens to the low/mid/high layers? | A provider fills a bundle whole or not at all: if any member is already taken, it fills none of the rest. With NWS first, the layers stay unavailable, the high-cloud penalty stays neutral, and Open-Meteo's total becomes an alternate. The README says listing NWS first costs the layer split. | User |
| D2 | NWS gridpoint data reaches about seven days. How far forward are periods expanded onto the hourly grid? | 72 hours from the start of the first period, the same reach as 7Timer!, so the timeline never grows because NWS was listed. | User |
| D3 | Does the points lookup from coordinates to grid cell run on every fetch? | The provider remembers each pier's grid cell in memory, keyed by coordinates. The first fetch makes two calls, later fetches one. A failed lookup is not remembered. A restart re-resolves. | User |
| D4 | Which NWS product supplies the data? | The raw gridpoint forecast, the only NWS product with numeric sky cover. It carries sky cover, wind speed, gust, direction, temperature, dew point, humidity and rain chance in variable-length periods. | Evidence: #155 body (periods expanded onto the hourly grid, total sky cover) |
| D5 | How is a pier outside NWS coverage reported? | The points lookup answers 404. `describe_error` already renders that as `HTTPStatusError: 404 Not Found`, and the fetch is a failed outcome passed over like any other. No startup check, as with the Open-Meteo models. | Evidence: `pierpressure/health.py`, `openspec/specs/conditions/spec.md` |
| D6 | What `User-Agent` does the provider send? | A fixed string of project name, running version from `pierpressure.__version__` and the repository URL. No email, no setting. | Evidence: #153 Shared decisions |
| D7 | What does the provider declare? | Key `nws`, display name `NWS`, no API key, variables `cloud_cover`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and `precipitation_probability`, no bundle. | Evidence: #155 body; the name is an assumption |
| D8 | Where does the issue time come from? | The gridpoint payload's `updateTime`, the forecast office's last edit. The recorded fixture confirms the field. | Assumption |
| D9 | What happens to a value whose unit code is not the one expected? | It is left absent, never converted. Expected codes: km/h for wind speed and gust, °C for temperature and dew point, percent for sky cover, humidity and rain chance, degrees for direction. | Assumption |
| D10 | Does the default provider list change? | No. NWS is US only, so `[open_meteo, seven_timer]` stays the default and adopters opt in. | Assumption |

## Changes from the story

Added: D1 tightens the fill for every provider, not only NWS. The rule "a bundle is filled from the same provider or not at all" was already in the spec and glossary, but the fill let a later provider complete a bundle an earlier one had started. NWS is the first provider that can trigger that path, so this story closes it.

Confirmed by user: yes
