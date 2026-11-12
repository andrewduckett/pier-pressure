## 1. Shared contracts

- [x] 1.1 [easy] A public `scored_window(instant, window)` in `core/scoring.py` returns the dark window clamped to start at the instant floored to a whole second (never past the end), `(None, None)` without a dark window; `evaluate` uses it, so every existing verdict test still passes (verify: uv run pytest tests/test_verdict_eval.py -q) (✓ uv run pytest tests/test_verdict_eval.py -q passed)
- [x] 1.2 [easy] `Target` requires a `remaining_window` (`TargetWindow`), declared right after `window`, so a serialized target lists `window` then `remaining_window` (verify: uv run pytest tests/test_target_model.py -q) (✓ uv run pytest tests/test_target_model.py -q passed)

## 2. Ranking on the remaining window [depends-on: 1]

- [x] 2.1 [complex] Ranking reads a night scan cached per pier id, location, horizon and dark window (equipment left out of the key, bound of 8): before dusk the target list is the same as today's apart from `remaining_window == window`; a later pre-dusk call in the same night does not rescan; two rigs on one pier share one scan but still score differently (design D2, D6) (verify: uv run pytest tests/test_ranking_pipeline.py -q) (✓ uv run pytest tests/test_ranking_pipeline.py -q passed; regenerated goldens equal the committed ones once `remaining_window` is removed)
- [x] 2.2 [complex] Once the night has started, ranking runs over the remaining grid (the scoring instant, then later grid points; design D3): a target already up gets `remaining_window.start == generated_at` and `remaining_window.end == window.end`; a target that has set, or has under 60 minutes left, is absent; 30 minutes before `dark_window.end` the list is empty (verify: uv run pytest tests/test_ranking_remaining.py -q) (✓ uv run pytest tests/test_ranking_remaining.py -q passed)
- [x] 2.3 [medium] The geometry factors read the remaining window (design D4): `geometry_for` at a mid-session instant returns the remaining window's peak altitude and the transit nearest its midpoint, a passed transit scores 0, a target up for the rest of the night has window factor 1, and the emitted `window`, `max_altitude`, `transit_time` and `moon_separation` keep their whole-night values (verify: uv run pytest tests/test_ranking_geometry.py -q) (✓ uv run pytest tests/test_ranking_geometry.py -q passed)
- [x] 2.4 [medium] With a horizon wall that hides a chosen target partway through the night, a ranking between its two stretches lists it with `window` on the first stretch and `remaining_window` on the second (verify: uv run pytest tests/test_ranking_remaining.py -q) (✓ uv run pytest tests/test_ranking_remaining.py -q passed; the test fails on the ranking before task 2.2)
- [ ] 2.5 [medium] A ranking at 23:00 after one at 21:00 in the same night does not rescan the catalog, and is byte-identical to a fresh 23:00 ranking with an empty cache (verify: uv run pytest tests/test_ranking_remaining.py -q)

## 3. Document, docs and the gate [depends-on: 2]

- [ ] 3.1 [medium] Regenerate the goldens with `PP_WRITE_GOLDENS=1`: every pre-dusk fixture differs from the committed one only by each target's added `remaining_window`, and the mid-session fixture's targets and "Top pick" line follow the remaining ranking (verify: uv run pytest tests/test_golden_verdict.py tests/test_producer_targets.py -q)
- [ ] 3.2 [easy] `docs/target-ranking.md` explains `remaining_window` and that ranking judges the rest of the night once it has started, and the README's `targets` row lists `remaining_window` (verify: uv run pytest tests/test_docs.py -q)
- [ ] 3.3 [easy] The whole project gate is green (verify: mise run check)

## Deviations Ledger

- 1.2: ranking sets `remaining_window` to `window` until task 2.1 computes it. From this commit until task 3.1 regenerates them, `tests/test_golden_verdict.py` fails, because the committed goldens lack the new key.
- 2.1: `test_the_equipment_joins_the_cache_key` is removed. Equipment has left the cache key (design D2), and `test_two_rigs_on_one_pier_share_a_scan_but_score_differently` now covers two rigs.
- 2.4: the spec scenario "A target with a second stretch ahead is ranked on it" had a first stretch (90 minutes) shorter than its second (120 minutes). Since `window` is the longest stretch, its THEN lines could not both hold. The times now make the first stretch the longer one, at 23:15. The test cuts the catalog to M31 and three rivals, so that M31 makes the list between its two stretches.
