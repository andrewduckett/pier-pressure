## 1. Config and the conditions snapshot contract

- [x] 1.1 Extend `PierConfig` with `go_threshold` (int 0–100, global default applied when omitted) and optional `max_gust` (wind gate disabled when omitted). Write the failing config tests first; verify `pytest tests/test_config.py` passes, including default-applied, omitted-gust-disables-gate, and range validation.
- [x] 1.2 Define the immutable `ConditionsSnapshot` data model in the pure core (`pierpressure/core/conditions.py`): an hourly series over the dark window with cloud, wind-gust, seeing, transparency slots, each stamped available/absent, plus a per-source issue time. Write model tests (construction, per-field availability, immutability); verify they pass and that `pytest tests/test_core_boundary.py` still passes (no HA/MQTT/network import in core).

## 2. Core verdict math (pure, deterministic, TDD)

- [x] 2.1 Implement the per-hour clarity weight `q(cloud)` and coverage weight `w` (fraction of the hour inside the dark window). Failing tests first; verify curve endpoints (clear→1, overcast→0) and that a fractional boundary hour yields `w<1`.
- [x] 2.2 Implement `W = Σ(w·q)` over hours with cloud data and the cloud score term `W / Σ_allh(w)`. Verify tests: term stays in [0,1] for non-whole-hour windows; uncovered cloud hours depress (never inflate or gate) the score.
- [x] 2.3 Implement clarity-weighted means for optional terms (denominator restricted to each term's available hours) and the moon term (per-hour above-horizon flag from M2's `moon.rise`/`set`, penalty = illumination × clarity-weighted up-fraction). Verify tests: a partial-coverage gap does not depress an optional mean; a bright moon up during darkness lowers the score.
- [x] 2.4 Implement the hard gates with precedence (no dark window; wind gust over `max_gust` at any hour; overcast = cloud available AND `W≈0`). Verify tests: each gate fires NO-GO with a null score and a naming reason; the overcast gate does NOT fire when cloud data is entirely absent.
- [x] 2.5 Implement score assembly (weighted combination of the terms, rounded to the nearest integer, clamped 0–100) and the GO/MAYBE split (GO iff `score ≥ go_threshold` AND cloud data present). Verify tests: threshold split; `go_threshold = 0` still needs cloud present for GO; a clear night scores higher than an identical clouded one.
- [x] 2.6 Implement confidence `max(floor, 100·L·F)·K` with the floor on `L·F` only, plus the astronomy-only NO-GO case (HIGH / 100). Verify tests: rises as dusk nears with freshness held equal; missing optional data lowers it without gating; missing cloud → value 0, band LOW; no-dark-window NO-GO → 100/HIGH.
- [x] 2.7 Implement the degradation precedence and `reasons[]` itemization: no-window → wind (incl. `max_gust` set but wind missing → cap MAYBE, never GO, trim `K`) → cloud entirely missing (MAYBE, score 0, confidence 0/LOW, "conditions unavailable" reason) → cloud present (overcast gate / score). Verify tests cover each rung, the fail-open-wind fix, and the missing-cloud MAYBE.
- [x] 2.8 Change `produce_verdict(pier, clock, conditions)` to assemble the document from 2.1–2.7 (filling the existing stubbed fields; no document reshape). Verify: a pinned fixture snapshot yields a byte-identical document across runs (`tests/test_determinism.py`), and `tests/test_core_boundary.py` / offline-guard still pass.

## 3. Conditions provider layer (outside the core; network lives only here)

- [x] 3.1 Define the provider interface and the snapshot assembly that merges provider outputs into a `ConditionsSnapshot` with per-field availability and per-source issue times. Verify unit tests build a snapshot from recorded fixture responses (no live network).
- [x] 3.2 Implement the base provider (Open-Meteo: hourly cloud + wind gust) parsing from a recorded fixture. Verify parsing tests map fixture JSON to the hourly slots.
- [x] 3.3 Implement the secondary provider (7Timer!: seeing + transparency, 3-hourly) and resample it onto the hourly grid in the provider layer. Verify tests: coarser cadence is resampled to hourly before the core sees it.
- [x] 3.4 Implement caching: reuse the last-good data per source when a fetch fails, within a max staleness, treating hours beyond a snapshot's forecast horizon as unavailable. Verify tests: recent data reused, over-stale treated unavailable, partial-horizon hours unavailable, base cache usable while the secondary is stale/absent.
- [x] 3.5 Implement independent fetch + graceful fallback (one source failing never fails the other; a partial snapshot is a valid result, not an error). Verify tests: secondary down leaves cloud/wind available; base down still returns a snapshot with cloud/wind marked unavailable.
- [x] 3.6 Add the HTTP client dependency with `uv add` (scoped to the provider layer). Verify `uv.lock`/`pyproject.toml` update together and the offline-guard test confirms the core still makes no outbound request.

## 4. Service wiring and delivery

- [x] 4.1 Have the persistent service fetch a conditions snapshot before calling `produce_verdict`, on startup, on interval, and on the on-demand refresh. Verify an integration test with a stub provider that a full recompute publishes a real (non-stub) verdict.
- [x] 4.2 Confirm the MQTT delivery surface is unchanged (existing fields filled, no reshape, no new entities). Verify `tests/test_discovery.py` and `tests/test_publish.py` still pass unchanged.

## 5. Tuning constants and the CI gate

- [x] 5.1 Choose sensible defaults for the deferred constants (clarity curve, `L`/`F` curves, band thresholds ~40/70, confidence floor, cache max-staleness, `go_threshold` default) and lock each with a test asserting representative inputs → expected outputs. Record the chosen values in `design.md` (resolving its Open Questions).
- [x] 5.2 Run the CI gate: `just check` (ruff lint + format, mypy strict, pytest) is green, including the determinism pinned-value tests and the core boundary/offline guards.
