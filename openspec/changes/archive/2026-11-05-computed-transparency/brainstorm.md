## Story

#159 computed-transparency — transparency is computed hourly from column water vapour and aerosol, as a source a pier can rank against 7Timer!
https://github.com/andrewduckett/pier-pressure/issues/159

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which Open-Meteo entries declare column water vapour? | Best match, HRRR and GFS; HRDPS, RDPS and ICON return none, so they do not declare it | Evidence: live Open-Meteo API, 2026-11-05 (`total_column_integrated_water_vapour`, kg/m²) |
| D2 | What is the computed source's key, and does it count for the keyless-cloud guard? | Catalog key `computed`; it needs no key, supplies no cloud and never satisfies the guard | Evidence: #159 Scope |
| D3 | How do water vapour and aerosol optical depth (AOD) reach the computed source? | By ordinary provider order, with no bundle; neither appears on the timeline | Evidence: #159 Scope; #153 Shared decisions; ADR 0030 |
| D4 | What scale does computed transparency use? | The core's `[0, 1]`, 1 best, the same scale 7Timer! is mapped onto | Evidence: `pierpressure/core/conditions.py`, `pierpressure/conditions/seven_timer.py` |
| D5 | Does `computed` join the default provider list? | Yes, appended last, after `open_meteo_air_quality`: it fills transparency only when 7Timer! returned none | User |
| D6 | An hour with one input but not the other? | That hour's computed transparency is blank; both inputs are needed | User |
| D7 | How does health show that no hour could be computed? | Status `failed`, with an error naming each missing input variable; any computed hour makes it `ok` | User |
| D8 | Which issue time does the computed series carry? | The oldest issue time among the input series it used | User |
| D9 | Does listing `computed` without its input providers stop startup? | No; it gives the failed, missing-input health outcome at run time | Evidence: #159 Scope |
| D10 | What is the water-vapour variable's key and unit? | `column_water_vapour`, kg/m², carried as reported | User |

## Changes from the story

None. The story stands as written; D5 to D8 settle behavior it left open.

Confirmed by user: yes
