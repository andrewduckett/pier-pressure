## 1. Golden safety net (characterize current behaviour before any refactor)

- [x] 1.1 Add a golden-output regression test that drives recorded raw Open-Meteo +
  7Timer! payloads through the provider layer → conditions → `produce_verdict` at a
  pinned instant, asserting the full verdict document equals a committed golden JSON.
  Route it through the provider so it is agnostic to the conditions type. Verify: the
  test passes against the current (unrefactored) flat-grid code.
- [x] 1.2 Extend the golden suite with the design-D4 cases, each a committed golden:
  both-present, secondary-absent, base-absent, base-returns-wind-without-cloud,
  gappy partial-window coverage, empty conditions, and over-stale cache. Verify: all
  cases pass against current code (goldens captured from known-good behaviour).

## 2. Per-source group model in the core

- [x] 2.1 Add `GroupMeta`, `BaseHour`, `SecondaryHour`, `BaseGroup`, `SecondaryGroup`
  (each group with an O(1) `.at(time)` lookup built like `_by_time`), and
  `Conditions(base, secondary)` to `core/conditions.py`, alongside the existing
  types for now. Verify: unit tests cover group construction, `.at(time)` hits/misses,
  and the canonical empty `Conditions(None, None)`.
- [x] 2.2 Encode the group-presence rule: a group is `None` iff its source returned no
  rows; a source that returned rows with all-`None` fields yields a present group.
  Verify: unit test asserts rows-but-empty-fields → present group; no rows → `None`.

## 3. Provider layer builds groups

- [x] 3.1 Change `conditions/provider.py` (`assemble_snapshot` + `CompositeProvider`)
  to build `Conditions` with `BaseGroup`/`SecondaryGroup` from the base/secondary
  `SourceForecast`s; base group present iff the base source returned rows, its
  `meta.issued_at` = the base issue time. Verify: provider tests assert group presence
  and `meta.issued_at` mirror today's `base_issued_at`/`secondary_issued_at`, including
  the base-present/secondary-absent and wind-without-cloud cases.
- [x] 3.2 Leave the 7Timer! provider-side hourly resample unchanged (design D3): the
  secondary group carries hourly-held values. Verify: existing 7Timer parse test still
  passes; secondary group hours are hourly-keyed.

## 4. Core reads groups

- [x] 4.1 Update `core/scoring.py` (freshness, completeness/`_field_coverage`,
  `optional_term_mean`, `clear_hours_total`, gates) and `core/producer.py` to read
  `Conditions` via each group's `.at(time)`, guarding `None` groups. Freshness reads
  `conditions.base.meta.issued_at` only (design D2) — never an oldest-of-groups helper.
  Verify: the full golden suite from group 1 passes byte-identical.
- [x] 4.2 Adapt determinism/verdict/scoring/producer tests to construct `Conditions`
  instead of `ConditionsSnapshot`. Verify: `just check` (ruff, mypy strict, pytest) is
  green.

## 5. Service seam

- [x] 5.1 Update `service.py`'s `ConditionsProvider` type alias and the `_no_conditions`
  fallback to `Conditions(None, None)`. Verify: service tests pass and the empty-conditions
  fallback yields the same astronomy-only verdict as before (a golden case).

## 6. Remove the superseded flat-grid model

- [x] 6.1 Delete `ConditionsSnapshot` and `HourlyConditions` and update every remaining
  reference. Verify: `just check` green and `grep -rn "ConditionsSnapshot\|HourlyConditions" pierpressure tests` returns nothing.

## 7. Delete the discarded M3 attempt

- [x] 7.1 Delete `pierpressure/core/verdict.py`, `pierpressure/providers/`,
  `tests/test_verdict.py`, `tests/test_conditions.py`, `tests/test_provider_*.py`, and
  `docs/adr/0005-conditions-as-injected-snapshot.md`. Verify: `just check` green and
  `git status` shows those untracked paths gone.

## 8. Final gate

- [x] 8.1 Run `just check` and confirm the whole golden suite is unchanged. Verify: the
  CI gate is green and every verdict document matches its committed golden byte-for-byte.
- [x] 8.2 Flip M3.5 to `status: done` in `docs/roadmap.md` in the landing PR (project
  convention). Verify: the merging PR shows M3.5 done.
