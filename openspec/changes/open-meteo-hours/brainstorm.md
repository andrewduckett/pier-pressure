**Why:** PierPressure asks Open-Meteo for whole days in UTC, so after midnight UTC the weather sensors drop every earlier hour and the strip's weather rows start at now.

## Story

#213 open-meteo-hours — Open-Meteo's weather covers the 4 hours before now and the 72 after, whatever the time in UTC.
https://github.com/andrewduckett/pier-pressure/issues/213

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does the story fit one change? | Yes. One request dictionary in `OpenMeteoProvider.fetch`, four test asserts, one spec requirement and four docs lines: five tasks. | Evidence: #213 Relevant code |
| D2 | Which requests change? | Every Open-Meteo request: best match, the five model providers and the air-quality endpoint. They share one request in `fetch`. | Evidence: `pierpressure/conditions/open_meteo.py` |
| D3 | What does each request ask for? | `past_hours: 4` and `forecast_hours: 72`, and no `forecast_days`. `timezone: UTC` and the km/h wind unit stay. | Evidence: #213 Scope |
| D4 | Do both endpoints accept these? | Yes. On 2026-11-08 at 03:13 UTC, best match, HRRR and air quality each returned 76 hours, 23:00 the day before to 02:00 three days on. | Evidence: live requests, 2026-11-08 |
| D5 | Why 4 hours back? | The strip opens 4 hours before dusk, and #214 makes it open 4 hours before now once the night has started. | Evidence: night-card spec; #214 Scope |
| D6 | What happens past a model's reach, such as HRRR at about 48 hours? | Open-Meteo returns nulls there. The series keeps those hours as blanks, and the next provider does not fill them, as the README already says. No code change. | Evidence: live HRRR request (26 nulls); `parse_open_meteo`; `README.md` "Hours past a model's reach stay empty"; plan review round 1 |
| D7 | Does a longer window strain delivery? | No. Each weather sensor's `forecast` grows to at most 76 points of about 50 bytes, well under Home Assistant's 16 KB attribute limit, and the timeline already reaches about 72 hours through 7Timer!. | Evidence: `pierpressure/delivery/mqtt.py` `timeline_attributes` |
| D8 | What do the tests assert? | The request's parameters, not the number of hours returned: Open-Meteo decides the rows, so a recorded fixture cannot prove them. | Assumption |
| D9 | Which spec changes? | The `conditions` spec. A new requirement says every Open-Meteo request asks for 4 past and 72 forecast hours. The model-provider scenarios that say "2 forecast days" now say the same. | Evidence: `openspec/specs/conditions/spec.md` |
| D10 | Which docs change? | `docs/night-card.md` says Open-Meteo reaches about three days, not two. In the README, the air-quality section and the model limits name the new window, not 2 days. The model table says ICON and GFS reach more than 3 days. | Evidence: #213 Scope; `README.md`; plan review round 1 |
| D11 | What about the unarchived `open-meteo-run-times` change? | Leave it alone. It adds a metadata request but does not change the forecast parameters; whichever lands second rebases one dictionary. | Evidence: `openspec/changes/open-meteo-run-times/tasks.md` |
| D12 | Does this need a glossary term? | No. "Fetch" and "forecast" keep their plain meanings. | Assumption |

## Changes from the story

Added: the README's air-quality section, its Open-Meteo model limits and its model table also name the 2-day window, so they change with `docs/night-card.md`.

Confirmed by user: yes
