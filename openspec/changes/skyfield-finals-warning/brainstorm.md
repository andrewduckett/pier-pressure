**Why:** From 18 October 2026 every start logs a warning that `finals2000A.all` has expired. PierPressure never reads that file, but users are told to check the log, and the warning will come back each year between a `skyfield-data` file expiring and its next release.

## Story

#211 skyfield-finals-warning — the log no longer warns about an expired file PierPressure never reads
(https://github.com/andrewduckett/pier-pressure/issues/211)

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does this change a spec, or is it a fix with no spec change? | It adds a requirement to `night-verdict`, beside "Astronomical fields are computed offline from bundled data". | User |
| D2 | Where does the warning come from? | `get_skyfield_data_path()` runs `check_expirations()` on every call. That check warns for each file the package ships whose date has passed, whether or not it is read. | Evidence: `skyfield_data/__init__.py`, `skyfield_data/expirations.py` |
| D3 | Filter the warning, or avoid it? | Avoid it. Find `de421.bsp` by its package location (`importlib.resources.files("skyfield_data") / "data" / "de421.bsp"`) and never call `get_skyfield_data_path()`. A filter would leave a message pattern to keep in step with upstream. | User |
| D4 | Do we lose a real signal along with the `de421.bsp` expiry check? | No. Its date, 2053-10-09, is where the ephemeris data ends, and Skyfield raises `EphemerisRangeError` for any date past it. | Evidence: run against Skyfield 1.55 for a date in 2060 |
| D5 | What if a future `skyfield-data` moves the file? | Loading fails at startup and in the tests, so CI catches it on the Renovate update. We accept this because the `data/` folder is not public API. | User |
| D6 | How do the four test modules find the ephemeris? | They call one helper in `pierpressure/core/sky.py` that returns the `de421.bsp` path, the same one `_ephemeris()` uses. The path is written in one place. | User |
| D7 | How does a test prove the warning is gone, whatever today's date? | Mark every file in `skyfield_data`'s expiry table as expired, then load the ephemeris with warnings raised as errors. The test passes because the check never runs. | User |
| D8 | What does the runbook say? | `docs/data-updates.md`'s known-warning section explains why PierPressure does not call `get_skyfield_data_path()`, and that a date outside the ephemeris's range fails with an error. | User |

## Changes from the story

- Cut: ignoring only the `finals2000A.all` expiry warning, and the test that another file's expiry warning still comes through. Avoiding the check leaves no filter to maintain (D3), and the `de421.bsp` date is already guarded by Skyfield's range error (D4).
- Added: `_ephemeris()` and the four test modules find `de421.bsp` by its package location, with a test that loading the ephemeris raises no warning, whatever today's date.
- Changed: the runbook section now explains the avoided check, not a filter.

Confirmed by user: yes
