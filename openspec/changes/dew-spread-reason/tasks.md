## 1. The setting

- [x] 1.1 [easy] `PierConfig.dew_margin` defaults to 4.0, stores a set value, and rejects a negative, `.inf` or `nan` value with an error naming the field, from a constructor and from `load_config` YAML (verify: `uv run pytest tests/test_config.py -k dew_margin`) (✓ `uv run pytest tests/test_config.py -k dew_margin` passed, 10 tests)

## 2. The dew line [depends-on: 1]

- [x] 2.1 [medium] `dew_reason(window, conditions, margin)` returns `Dew likely from <iso_z slot start>.` for the first scored hour slot whose temperature minus dew point is strictly under the margin, `Frost likely from …` when that hour is at or below 0 °C, and `None` when the margin is 0, when a spread equals the margin, or when no hour qualifies (verify: `uv run pytest tests/test_scoring.py -k dew_reason`) (✓ `uv run pytest tests/test_scoring.py -k dew_reason` passed, 7 tests)
- [x] 2.2 [easy] `dew_reason` skips an hour missing temperature or dew point, names a mid-session boundary slot by its top-of-hour start, never names a slot before the scored window, and ignores cloud (verify: `uv run pytest tests/test_scoring.py -k "dew_reason and (skips or boundary or cloud)"`) (✓ `uv run pytest tests/test_scoring.py -k "dew_reason and (skips or boundary or cloud)"` passed, 4 tests; each fails against a mutated walk)
- [x] 2.3 [medium] `evaluate` appends the dew line last on a scored verdict, after any cap line and the agreement line, and on the missing-cloud `MAYBE`; a gated `NO-GO` carries none; the existing agreement-tail test stays green (verify: `uv run pytest tests/test_scoring.py -k "dew_line or agreement"`) (✓ `uv run pytest tests/test_scoring.py -k "dew_line or agreement"` passed, 34 tests)
- [x] 2.4 [easy] Two snapshots differing only in temperature and dew point give identical `verdict`, `score` and `confidence`, and reasons that differ by at most one dew or frost line (verify: `uv run pytest tests/test_scoring.py -k dew_changes_nothing_else`) (✓ `uv run pytest tests/test_scoring.py -k dew_changes_nothing_else` passed, 3 cases)

## 3. Goldens and docs [depends-on: 2]

- [x] 3.1 [medium] Golden cases `dew_night` and `frost_night` built from the recorded Open-Meteo payload with temperature and dew point added, so one document pins the dew line at 22:00 UTC and the other the frost line at 00:00 UTC; existing goldens are byte-identical (verify: `uv run pytest tests/test_golden_verdict.py`) (✓ `uv run pytest tests/test_golden_verdict.py` passed, 11 tests; no existing golden changed)
- [x] 3.2 [parallel] [easy] README documents `dew_margin` in the pier example and the settings table, and `ha-addon/DOCS.md` says it is set in the add-on's `config.yaml` file; the conditions module docstring no longer says nothing reads the weather variables (verify: `grep -q dew_margin README.md ha-addon/DOCS.md`) (✓ `grep -q dew_margin README.md ha-addon/DOCS.md` passed)
- [x] 3.3 [easy] The full gate is green (verify: `mise run check`) (✓ `mise run check` passed, 1808 tests)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-04: `test_producer_targets` checks every `_CASES` entry against a file in `tests/fixtures/golden/stub/`, so the two new cases gained stub baselines, written from the same expression the test uses. The plan named only the goldens.
- 2026-11-04: `test_weather_variables_do_not_change_the_verdict` in `tests/test_producer_timeline.py` assumed no term reads the weather variables. It now expects the one dew line, then compares the rest of the document as before.
