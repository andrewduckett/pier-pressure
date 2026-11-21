**Why:** The horizon-mask spec still says the horizon has no consumer and leaves `targets` empty, but target ranking has filtered targets by the horizon since it shipped, and the top pick's sentences in `reasons` follow the filtered list, so the two specs now contradict each other and mislead anyone who reads the horizon-mask spec.

## Story

#273 horizon-mask-targets-drift — the horizon-mask spec says the horizon changes targets,
https://github.com/andrewduckett/pier-pressure/issues/273

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does a configured horizon change the verdict document today? | Yes: `rank_targets` drops candidates that do not clear `pier.horizon_mask`, so `targets` differs. `produce_verdict` then adds the top pick's sentences (the framing sentence and the bright-target sentence) to `reasons` from `targets[0]`, so a horizon that changes or removes the top pick can change those sentences too. Every other field and every other reason is unchanged. | Evidence: `pierpressure/core/ranking.py`, `pierpressure/core/producer.py`, Gemini Neon code review of PR #314, confirmed by the user |
| D2 | How should the corrected requirement word what the horizon changes? | It changes only `targets` and, through the top pick, the top-pick sentences in `reasons`; every other field and every other reason stays identical. It SHALL NOT add, remove or reshape any field, topic or entity, and entities fed by `targets` and `reasons` show their new values: the verdict sensor's attributes, the top-target and rank sensors (which go `unavailable` when a rank empties), and the narrative (produced afresh when the targets it explains or the reasons change). This supersedes the first answer, which said only `targets` changes. | User (change request on PR #314) |
| D3 | Should the requirement keep its name "The horizon mask has no consumer in the verdict document"? | No: rename it (a RENAMED plus MODIFIED delta), for example to "The horizon mask changes only the targets and the top-pick reasons". D8 says how. | Assumption |
| D4 | Should this change also fix the spec's Purpose, which says a "later milestone" will rank out targets? | Yes: edit that one sentence in `openspec/specs/horizon-mask/spec.md` directly, because a delta cannot change a Purpose. | Assumption |
| D5 | What does the new scenario assert? | Two verdicts for one pier, instant and conditions, one with a horizon that hides a target listed without it, and neither carrying a top-pick sentence: their `targets` differ, and every other field is identical. The precondition matches the existing test, whose top picks earn no top-pick sentence. | User (change request on PR #314); Evidence: `tests/test_horizon_contract.py` |
| D6 | Does this change need new code or tests? | No: `tests/test_horizon_contract.py::test_horizon_changes_only_targets` asserts the scenario in D5. It compares the two documents as parsed JSON with `targets` removed, so it proves the case with no top-pick sentence, not the top-pick sentences changing. The build only runs the checks. | Evidence: #273 scope, `tests/test_horizon_contract.py` |
| D7 | Does target-ranking's horizon requirement change? | No: "A target must clear the horizon mask for the minimum duration" already matches the code and stays as it is. | Evidence: #273 scope, `openspec/specs/target-ranking/spec.md` |
| D8 | How does the spec delta make the rename in D3, given that OpenSpec 2.0.0 rejects a MODIFIED block that drops the old scenario name? | REMOVED plus ADDED: remove "The horizon mask has no consumer in the verdict document" with a reason and a migration note, and add "The horizon mask changes only the targets and the top-pick reasons" with the scenario "A horizon that changes no top-pick sentence changes only the targets". The requirement moves to the end of the main spec. This supersedes the RENAMED plus MODIFIED form in D3. | Assumption |
| D9 | Should the spec add a second scenario for a horizon that changes the top-pick sentences? | No: a scenario needs a test that asserts it, and #273 allows no test change. The requirement states the rule; a follow-up issue can add the test and the scenario together. | Assumption |
| D10 | What should the corrected Purpose say target ranking uses the horizon for? | To leave out targets that never clear it or clear it for less than the minimum duration, and to bound each listed target's window. | User (change request on PR #314) |

## Changes from the story

- Added: the Purpose sentence in `openspec/specs/horizon-mask/spec.md` is corrected too (D4). It is the same drift, and the issue excludes only code, tests and target-ranking requirements.
- Clarified: the issue's "It changes no other field, topic or entity" becomes "changes only `targets` and the top-pick sentences in `reasons`, and adds, removes or reshapes no field, topic or entity" (D1, D2). Entities fed by `targets` and `reasons` show their new values even though no topic or entity changes.

Confirmed by user: yes
