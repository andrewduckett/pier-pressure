## Story

#160 computed-seeing — seeing is computed hourly from bad layers, jet-stream speed and boundary-layer height
https://github.com/andrewduckett/pier-pressure/issues/160

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which Open-Meteo models carry the seeing column? | Best match and GFS carry every level, the 300 hPa wind and boundary-layer height; HRRR lacks only 70 and 30 hPa; ICON, RDPS and HRDPS send no boundary-layer height, and HRDPS covers 43 of 48 hours | Evidence: live Open-Meteo API, 2026-11-05 (`temperature_<p>hPa`, `geopotential_height_<p>hPa`, `wind_speed_300hPa`, `boundary_layer_height`) |
| D2 | Which models declare the seeing column? | Best match, HRRR and GFS only, boundary-layer height included; HRDPS, RDPS and ICON do not | User |
| D3 | What is in the seeing-column bundle? | Temperature and geopotential height at the 17 levels those three share (1000 to 50 hPa, not 70 or 30), the 300 hPa wind speed and boundary-layer height | Evidence: D1; #160 Scope |
| D4 | What counts as a bad layer? | A strongly stable layer between two levels: one whose temperature falls by less than 0.476 K per 100 m, or rises. This is a potential-temperature rise of more than 0.5 K per 100 m measured at 1000 hPa, so the test is the same at every height | User (revised after the plan review, round 1) |
| D5 | Which layers are counted? | Only layers above the pier's ground and below the tropopause; the design picks how to find the tropopause | User |
| D6 | What jet-stream speed counts as bad? | The 300 hPa wind speed, when above 35 m/s or below 5 m/s | Evidence: #160; #153 What was found |
| D7 | What does the index promise? | A value in `[0, 1]`, 1 best, that never rises with more bad layers, with a jet further outside 5 to 35 m/s, or with a deeper boundary layer | Evidence: #160 Scope; User for the boundary-layer direction |
| D8 | Does the default provider list change? | No; `computed` stays last, so 7Timer!'s seeing wins and computed seeing fills only when 7Timer! returns none | Evidence: ADR 0031; #159 brainstorm D5 |
| D9 | One computed variable works and the other does not? | Health status `ok`, and the error names the variable that failed and why | User |
| D10 | Both computed variables fail? | Status `failed`; the error lists each failure prefixed by its variable, transparency first, which rewords today's transparency-only errors | User |
| D11 | Which issue times are used? | Each computed series carries the oldest issue time of its own inputs; the health record carries the oldest across the computed series | User |
| D12 | How does health show which model fed the index? | A new `inputs` attribute on the computed health record maps each computed variable to the providers that fed it on the last success | User |
| D13 | Do the raw column variables reach the timeline? | No; they are raw variables | Evidence: ADR 0030; #153 Shared decisions |
| D14 | Are calibration and arcsecond output in scope? | No | Evidence: #160 Scope |

## Changes from the story

None. D9 to D12 settle behavior the story left open, including the open
question that computed-transparency's design passed to this story. The
glossary's Bundle entry now names the seeing column.

Confirmed by user: yes
