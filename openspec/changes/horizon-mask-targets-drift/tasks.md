## 1. Correct the horizon-mask spec

- [ ] 1.1 [easy] Confirm that the existing test `test_horizon_changes_only_targets` asserts the new scenario "A horizon that hides a target changes only the targets": the two verdicts' `targets` differ and every other field is byte-identical. Change no code or test; if the test does not pass, stop and report (verify: uv run pytest tests/test_horizon_contract.py)
- [ ] 1.2 [easy] In `openspec/specs/horizon-mask/spec.md`, rewrite the end of the Purpose sentence, "so a later milestone can rank out targets that never clear it", to say that target ranking uses the horizon to leave out targets that never clear it. Change no requirement in the main spec; the delta changes the requirement at archive (verify: mise run specs)
- [ ] 1.3 [easy] Run the full gate on the branch (verify: mise run check)
