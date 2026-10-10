## 1. Config: the `equipment` key and the `Equipment` class

- [x] 1.1 Write failing tests in `tests/test_equipment.py`: a pier loads with an `equipment:` block and exposes it as `pier.equipment`; `Equipment` validates as `Rig` does today; a pier with a `rig:` block fails validation; and `validate_piers` skips that pier while a second valid pier survives. Verify the tests fail because `Equipment` and `PierConfig.equipment` do not exist yet.
- [x] 1.2 Rename `Rig` to `Equipment` and `PierConfig.rig` to `PierConfig.equipment` in `pierpressure/core/config.py`, and follow the rename through `ranking.py`, `producer.py`, and every test that builds or reads one. Rename identifiers per design D1: for example `_rig_key` becomes `_equipment_key`, the `rig` parameter becomes `equipment`, and `_WIDEFIELD_RIG` becomes `_WIDEFIELD_EQUIPMENT`. Verify the 1.1 tests pass and `just check` is green.

## 2. Verdict: the four framing sentences

- [ ] 2.1 Write failing tests that pin each sentence exactly (design D3). In `tests/test_ranking_suitability.py`, assert that M31 (catalog name "Andromeda Galaxy") at 8, 60, 270, and 600 mm yields exactly "Top pick Andromeda Galaxy is small in your field of view.", "… frames well in your field of view.", "… fills most of your field of view.", and "… is larger than your field of view.". In `tests/test_producer_targets.py`, replace the `"rig" in r.lower()` check with an exact match on one of the four sentences for the top pick. Verify the tests fail on the current wording.
- [ ] 2.2 Change the four sentences in `equipment_reasons` in `pierpressure/core/ranking.py`. Verify the 2.1 tests pass, `tests/test_golden_verdict.py` passes, and `git diff --stat tests/fixtures` shows no change.

## 3. Docs

- [ ] 3.1 Write a failing test that loads the README's pier config example (the fenced YAML block under the config section) through `validate_piers` and checks that the pier has equipment. Verify it fails while the example still says `rig:`.
- [ ] 3.2 Update `README.md`: the config example uses `equipment:`, and the settings table row becomes `equipment`, with "With equipment, targets are also ranked…". Verify the 3.1 test passes.
- [ ] 3.3 Update `openspec/prd.md` (lines 105 and 130) and `openspec/discovery.md` (lines 16, 31, and 78) to say "equipment" where they name the entity. Verify by reading each changed line in the diff.

## 4. Sweep

- [ ] 4.1 Search the live tree with `grep -rnwi -e rig -e rigs pierpressure tests README.md openspec --exclude-dir=archive`, excluding `docs/decisions/`. Check each remaining hit against design D1: only informal prose may keep "rig". The two target-ranking scenario titles are left for the archive commit. Verify `just check` is green.

## Archive note

When archiving, keep the archive as the last commit (design D4). In the same commit, after the delta sync, edit the main specs directly:

- In `openspec/specs/target-ranking/spec.md`, rename "A well-framed target ranks higher when a rig is configured" to "A well-framed target ranks higher when equipment is configured", and "A rig change changes the ranking" to "An equipment change changes the ranking".
- In `openspec/specs/pier-equipment/spec.md`, reword the Purpose to say "equipment" in place of "rig".
