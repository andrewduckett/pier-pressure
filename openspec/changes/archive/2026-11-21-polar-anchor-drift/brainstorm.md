**Why:** The night-verdict spec anchors continuous polar night to the local solar day, but at exactly ±90° latitude the code falls back to the UTC calendar day, and no requirement says so, so the spec no longer describes the dark window a pier at a pole gets.

## Story

#275 polar-anchor-drift — the night-verdict spec states the UTC-day anchor at the exact poles
https://github.com/andrewduckett/pier-pressure/issues/275

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | Spec the fallback to the UTC calendar day at exactly ±90° latitude, with a scenario a test asserts. The fallback in `_local_solar_day` stays as it is, and no other latitude is covered. | Evidence: #275 issue body (Scope) |
| D2 | What does the code do at the poles? | When `abs(latitude) == 90.0` and the night is continuous, the anchor runs from 00:00 UTC of the evaluation instant's UTC date to 00:00 UTC the next day. The evaluation instant is always UTC, because the clock converts it. | Evidence: `pierpressure/core/sky.py` (`_local_solar_day`), `pierpressure/core/clock.py` |
| D3 | Does the spec add a requirement or modify the existing anchor requirement? | Add one requirement, "At the exact geographic poles, the continuous-night anchor is the UTC calendar day". It says that at exactly 90° or −90° latitude the day that anchors continuous polar night is the UTC calendar day holding the evaluation instant, in place of the local solar day, wherever the night-verdict spec names that day. No existing requirement is modified. | Assumption |
| D4 | Which scenarios does the new requirement get? | Two: at latitude 90° in December polar night, at 12:00 UTC, `dark_window` runs from 00:00 UTC that day to 00:00 UTC the next day; the same holds at latitude −90° in June polar night. | Assumption |
| D5 | Which tests assert the scenarios? | The existing pole test, `test_exact_pole_falls_back_to_utc_day_anchor` in `tests/test_sky_dark_window.py`, asserts the north-pole case. Parametrize it to add the south pole on 21 June 2026, so both ±90° cases are asserted. | Assumption |
| D6 | How is each test shown to fail first? | The fallback already exists, so the build briefly disables the ±90° branch in `_local_solar_day`, watches the pole tests fail, then restores the code unchanged. | Assumption |
| D7 | Does the change cover the timeline hours at the poles? | No. The timeline's hours also use `_local_solar_day`, so at the poles they follow the UTC day too, but the timeline is a separate requirement and outside #275. | Assumption |

## Changes from the story

None.

Confirmed by user: yes
