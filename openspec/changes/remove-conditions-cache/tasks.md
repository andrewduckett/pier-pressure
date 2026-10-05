Practice TDD: write the failing test first, then change the code. `just check`
(ruff lint, mypy strict, pytest) is the CI gate and must be green before the PR is
marked ready. Mentions of the explainer's cache and the ranking's per-night cache are
a different thing and stay unchanged.

## 1. Failed fetches are not filled from earlier fetches

- [x] 1.1 Give `build_provider()` optional `base` and `secondary` source arguments that default to the real providers, so tests can run the production stack with stub sources. Verify that existing tests pass.
- [x] 1.2 In `tests/test_conditions_provider.py`, write the same-pier regression test from design D1: through `build_provider()` with stub sources, a successful fetch and then a failed fetch for the same pier. Assert the failed snapshot's base group is `None`. Repeat with an empty fetch in place of the failure. Verify the test fails against the current cache (spec: "A failed fetch is not filled from an earlier fetch").
- [x] 1.3 Write the two-pier regression test from design D1: a successful fetch for pier A, then a failed or empty fetch for pier B through the same stack. Assert pier B's base group is `None`. Verify the test fails against the current cache (spec: "A failed fetch for one pier is not filled from another pier's fetch").
- [x] 1.4 Remove `CachingProvider` and `MAX_STALENESS` from `pierpressure/conditions/provider.py`. Make `build_provider()` pass `OpenMeteoProvider()` and `SevenTimerProvider()` straight to `CompositeProvider`. Remove the exports from `pierpressure/conditions/__init__.py`. Verify that tests 1.2 and 1.3 pass (design D1).

## 2. Tests that depended on the cache

- [x] 2.1 Delete `test_cache_reuses_recent_data_after_a_failed_fetch`, `test_cache_drops_over_stale_data`, and `test_cache_is_per_source_so_base_survives_secondary_outage` from `tests/test_conditions_provider.py`. Keep `test_forecast_horizon_beyond_the_data_is_unavailable`. Verify that `test_secondary_failure_leaves_base_data_intact` still covers one source failing while the other survives.
- [x] 2.2 Delete `test_cache_max_staleness_is_twelve_hours` and its `MAX_STALENESS` import from `tests/test_tuning_constants.py`. Verify that the file's other tests pass.
- [x] 2.3 In `tests/test_golden_verdict.py`, rename the `over_stale_cache` case to `stale_issued_base` and build it directly with `_base_full(issued_at=_STALE_ISSUED)`. Delete `_over_stale_base` and `_StubProvider`. `git mv` both golden files to `stale_issued_base.json`, in `tests/fixtures/golden/expected/` and `tests/fixtures/golden/stub/`, without changing their contents. Verify that `tests/test_golden_verdict.py` and `tests/test_producer_targets.py` pass with no golden regenerated (design D3).

## 3. Comments and docstrings

- [ ] 3.1 Reword the module docstrings in `pierpressure/conditions/provider.py` and `pierpressure/conditions/__init__.py` so they describe graceful fallback with no cache. Reword the "fetches, fails, caches" docstring in `pierpressure/core/conditions.py`. Verify with `git grep -n -i cach -- pierpressure/conditions pierpressure/core/conditions.py`, which must return nothing.
- [ ] 3.2 Reword the freshness comment in `pierpressure/core/scoring.py` so the 12-hour point is the age at which base data reaches the freshness floor, with no mention of the cache. Leave every constant unchanged. Verify that `tests/test_tuning_constants.py` passes (design D2).

## 4. Durable constraint and docs

- [ ] 4.1 Change "caching and graceful fallback" to "graceful fallback" in the durable constraint in `AGENTS.md`, `openspec/config.yaml`, and `openspec/prd.md`. Verify by reading each changed line in the diff.
- [ ] 4.2 Remove "caching" from the two conditions lines in `README.md` and from the *Notice a provider breaking* stage in `openspec/discovery.md`. Verify by reading each changed line in the diff, and verify that `tests/test_docs.py` passes.
- [ ] 4.3 Edit ADR 0005 in place: remove "caching" from the Decision paragraph, and replace "A provider outage is buffered by cache" with a line saying an outage shows as missing data and lower confidence, not a crash. Add a dated note at the end that names this change and says why. Keep its status `accepted`. Verify by reading the rendered ADR (design D4).
- [ ] 4.4 Search the repo with `git grep -n -i cach -- ':!openspec/changes'`. Verify that every remaining hit is the explainer's cache, the ranking's per-night cache, the catalog loader, a Docker or `.gitignore` entry, ADR 0004, or deprecated ADR 0006.

## 5. Gate

- [ ] 5.1 Run `just check` and verify that ruff, mypy, and pytest are all green.
