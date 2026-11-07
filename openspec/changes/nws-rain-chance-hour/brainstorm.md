**Why:** On a pier where NWS supplies rain chance, every value shows one hour early on the Rain chance sensor and the card, because the NWS parser puts it on the hour its period starts instead of the hour that period ends.

## Story

#201 nws-rain-chance-hour — NWS rain chance lands on the hour it describes, not an hour early
https://github.com/andrewduckett/pier-pressure/issues/201

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which NWS variables move? | Only `precipitation_probability`; every other NWS variable stays on the hours its period starts at, because they are values at the start of each hour. | Evidence: `docs/night-timeline.md` (rain chance is for the hour that ends at `time`) |
| D2 | Where does the shift happen? | In `parse_nws`, for rain chance alone; `_hours` stays shared and unchanged. | Evidence: `pierpressure/conditions/nws.py` (`_hours` serves every variable) |
| D3 | Which hours does a rain chance period fill? | Each hour its period covers, one hour later: `18:00/PT6H` fills 19:00 to 00:00. | Evidence: #201 packet |
| D4 | Does the timeline doc's rain chance row change here? | No. It stays out of this change; a separate chore makes the whole variable table name sources and thresholds without assuming Open-Meteo. | User |
| D5 | Is a shifted hour cut at the 72-hour horizon? | Yes. The horizon is still measured from the earliest unshifted period start, and a shifted hour at or past it is dropped, so NWS never lengthens the timeline. | User |
| D6 | How is a period that does not start on the hour handled? | Shift the hours `_hours` already returns by one hour; NWS periods start on the hour in practice. | User |
| D7 | What proves the fix? | A test on `tests/fixtures/nws_gridpoints.json`: the first rain chance hour is one hour after the first `probabilityOfPrecipitation` period start, and the other variables keep their hours. Plus a unit test of the horizon cut. | Evidence: #201 packet |

## Changes from the story

- Split out: the timeline doc's variable table names each variable's source and rain chance threshold without assuming Open-Meteo, filed as #202.

Confirmed by user: yes
