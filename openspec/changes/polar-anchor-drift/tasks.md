## 1. Test the UTC-day anchor at the exact poles

The code already falls back to the UTC calendar day at exactly ±90° latitude
(`_local_solar_day` in `pierpressure/core/sky.py`). Do not change that
fallback or any other code under `pierpressure/`, and do not test any other
latitude.

- [x] 1.1 [easy] Confirm that the existing test `test_exact_pole_falls_back_to_utc_day_anchor` in `tests/test_sky_dark_window.py` covers the scenario "At the north pole in December, the dark window is the UTC day": latitude 90, longitude 0, instant 2026-12-21T12:00:00Z, and a dark window from 2026-12-21T00:00:00Z to 2026-12-22T00:00:00Z. Change no code or test; if the test does not pass, stop and report (verify: uv run pytest tests/test_sky_dark_window.py -k exact_pole) (✓ uv run pytest tests/test_sky_dark_window.py -k exact_pole passed: 1 passed)
- [x] 1.2 [easy] Parametrize `test_exact_pole_falls_back_to_utc_day_anchor` over both poles, keeping the north-pole case from 1.1 unchanged and adding the scenario "At the south pole in June, the dark window is the UTC day": latitude −90, longitude 0, instant 2026-06-21T12:00:00Z, and a dark window from 2026-06-21T00:00:00Z to 2026-06-22T00:00:00Z. Because the code already passes it, prove both cases can fail: turn off the `abs(pier.latitude) == 90.0` branch in `_local_solar_day`, watch both cases fail, then restore the code exactly (verify: uv run pytest tests/test_sky_dark_window.py -k exact_pole) (✓ uv run pytest tests/test_sky_dark_window.py -k exact_pole passed: 2 passed; with the branch off, both cases failed with IndexError; sky.py restored, git diff empty)
- [x] 1.3 [easy] Check that the branch changes no code under `pierpressure/`, so the pole fallback stays as it was (verify: git diff --exit-code top-pick-sentences-drift -- pierpressure/) (✓ git diff --exit-code top-pick-sentences-drift -- pierpressure/ passed: no diff)
- [x] 1.4 [easy] Check that the change's spec delta passes strict validation (verify: openspec validate polar-anchor-drift --strict) (✓ openspec validate polar-anchor-drift --strict passed)
- [ ] 1.5 [easy] Run the full gate on the branch (verify: mise run check)
