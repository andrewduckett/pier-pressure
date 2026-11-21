**Why:** The horizon-mask spec still says the horizon has no consumer and leaves `targets` empty, but target ranking has filtered targets by the horizon since it shipped, so the two specs now contradict each other and mislead anyone who reads the horizon-mask spec.

## Story

#273 horizon-mask-targets-drift — the horizon-mask spec says the horizon changes targets,
https://github.com/andrewduckett/pier-pressure/issues/273

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does a configured horizon change the verdict document today? | Yes: `rank_targets` drops candidates that do not clear `pier.horizon_mask`, so `targets` differs; every other document field is byte-identical. | Evidence: `pierpressure/core/ranking.py`, `tests/test_horizon_contract.py` |
| D2 | How should the corrected requirement word what the horizon changes? | It changes only the `targets` field of the verdict document and adds, removes or reshapes no field, topic or entity; entities that display `targets` show the changed list. | Assumption |
| D3 | Should the requirement keep its name "The horizon mask has no consumer in the verdict document"? | No: rename it (a RENAMED plus MODIFIED delta), for example to "The horizon mask changes only the targets in the verdict document". | Assumption |
| D4 | Should this change also fix the spec's Purpose, which says a "later milestone" will rank out targets? | Yes: edit that one sentence in `openspec/specs/horizon-mask/spec.md` directly, because a delta cannot change a Purpose. | Assumption |
| D5 | What does the new scenario assert? | Two verdicts for one pier, instant and conditions, one with a horizon that hides a target listed without it: their `targets` differ, and every other field is byte-identical. | Evidence: `tests/test_horizon_contract.py` |
| D6 | Does this change need new code or tests? | No: `tests/test_horizon_contract.py::test_horizon_changes_only_targets` already asserts the corrected behavior; the build only runs the checks. | Evidence: #273 scope, `tests/test_horizon_contract.py` |
| D7 | Does target-ranking's horizon requirement change? | No: "A target must clear the horizon mask for the minimum duration" already matches the code and stays as it is. | Evidence: #273 scope, `openspec/specs/target-ranking/spec.md` |

## Changes from the story

- Added: the Purpose sentence in `openspec/specs/horizon-mask/spec.md` is corrected too (D4). It is the same drift, and the issue excludes only code, tests and target-ranking requirements.
- Clarified: the issue's "It changes no other field, topic or entity" becomes "changes only the `targets` field and adds, removes or reshapes no field, topic or entity" (D2). The top-target and rank sensors and the narrative display `targets`, so their state follows the list even though no topic or entity changes.

Confirmed by user: no
