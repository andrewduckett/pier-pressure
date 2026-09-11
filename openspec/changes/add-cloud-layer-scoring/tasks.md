## 1. Conditions model: carry the low/mid/high split

- [ ] 1.1 In `tests/test_conditions_model.py`, add a failing test that a `BaseHour` carries `cloud_low`, `cloud_mid`, and `cloud_high`, each an independently optional `float | None` defaulting to `None`, and that an hour with only some components set leaves the others `None`. Verify the test fails before the model changes.
- [ ] 1.2 Add `cloud_low`, `cloud_mid`, `cloud_high` fields (`float | None = None`) to `BaseHour` in `pierpressure/core/conditions.py`, mirroring the `cloud_cover`/`wind_gust` idiom, and update the class docstring to describe the components as percent, independently present-or-absent. Verify `tests/test_conditions_model.py` passes and `just check` stays green (frozen-dataclass immutability and the core boundary test still hold).

## 2. Provider seam: thread the components through

- [ ] 2.1 In `tests/test_conditions_provider.py`, add a failing test that `SourceReading` accepts the three component values and that `assemble_snapshot` copies them onto the resulting `BaseHour`, including the total-only case where the components are `None`. Verify it fails first.
- [ ] 2.2 Add `cloud_low`, `cloud_mid`, `cloud_high` (`float | None = None`) to `SourceReading` in `pierpressure/conditions/provider.py`, and map them onto `BaseHour` in `assemble_snapshot`. Verify `tests/test_conditions_provider.py` passes, including that a source returning only a total still yields a present group with `None` components.

## 3. Open-Meteo source: fetch and parse the components

- [ ] 3.1 Extend `tests/fixtures/open_meteo.json` (or add a component-carrying fixture) with `cloud_cover_low`/`cloud_cover_mid`/`cloud_cover_high` hourly arrays, including at least one hour with a `null` component to exercise the absent path.
- [ ] 3.2 In `tests/test_conditions_provider.py` (or the open-meteo parser test), add a failing test that `parse_open_meteo` maps the three component arrays onto `SourceReading`, leaving a missing/`null` component as `None`. Verify it fails first.
- [ ] 3.3 In `pierpressure/conditions/open_meteo.py`, add `cloud_cover_low,cloud_cover_mid,cloud_cover_high` to the `hourly` request params and parse each array into `SourceReading` (reusing `_as_float`, index-guarded like `cloud`/`gust`). Verify the parser test passes and no network is hit (fixture-driven).

## 4. Scoring: the distinct high/thin-cloud penalty

- [ ] 4.1 In `tests/test_scoring.py`, add a failing unit test for a new `high_cloud_penalty(window, conditions)` that: returns the clarity-weighted (`w·q`) mean of `cloud_high/100` over hours carrying **both** `cloud_cover` and `cloud_high`; restricts the denominator to those same hours (a partial-coverage window is not diluted); and returns `None` when no hour qualifies (design D2). Verify it fails first.
- [ ] 4.2 Implement `high_cloud_penalty` in `pierpressure/core/scoring.py`, modelled on `optional_term_mean` (restricted denominator, `None` when empty) — not on `moon_penalty` — and add `_HIGH_CLOUD_MAX_PENALTY` to the tuning-constant block. Verify 4.1 passes.
- [ ] 4.3 In `tests/test_scoring.py`, add a failing test that `assemble_score` folds the penalty in as an independent multiplicative factor `(1 - _HIGH_CLOUD_MAX_PENALTY * penalty)`, treating a `None` penalty as factor 1. Assert monotonicity: holding total `cloud_cover` and every other input fixed, more `cloud_high` yields a score that is lower or equal, never higher (night-verdict spec). Verify it fails, then wire the factor into `assemble_score` and confirm it passes.
- [ ] 4.4 In `tests/test_scoring.py`, add tests that the high-cloud term never gates: with high cirrus present and every hard gate passing, `evaluate` returns a non-`NO-GO` verdict with a non-null score in `[0, 100]`; and that when `cloud_high` is unavailable for the window, no high-cloud penalty is applied and no high-cloud reason line appears (night-verdict spec scenarios). Verify the tests pass.
- [ ] 4.5 Add the itemized high-cloud reason to `_score_reasons` in `pierpressure/core/scoring.py`, distinct from the `Cloud:` line and guarded by `penalty is not None and round(penalty * 100) > 0` (design D3). In `tests/test_scoring.py`, assert the reason appears as its own line when the rounded penalty exceeds 0 and is absent (no `High cloud penalty 0%`) for a sub-half-percent penalty. Verify the tests pass.
- [ ] 4.6 In `tests/test_tuning_constants.py`, assert `_HIGH_CLOUD_MAX_PENALTY` is present, is a fixed constant in `(0, 1)`, and (per design D2) is below `_MOON_MAX_PENALTY`. Verify the test passes.

## 5. Re-base the golden output and gate

- [ ] 5.1 Re-run `tests/test_golden_verdict.py`, confirm the only diff is the legitimately changed score/reasons on the high-cirrus scenario(s), and update the golden fixture under `tests/fixtures/golden/` once. Verify the golden test passes and the diff is limited to the expected fields.
- [ ] 5.2 Confirm determinism and offline guarantees are intact: `tests/test_determinism.py`, `tests/test_golden_verdict.py`, `tests/test_core_boundary.py`, and `tests/test_offline_guard.py` all pass (the new term is pure math over existing inputs; confidence and gates are unchanged).
- [ ] 5.3 Run `just check` (ruff lint + format, mypy strict, pytest) and verify the whole suite is green before opening the PR.
