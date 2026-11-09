## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario. A probe under `.workspace/` showed it: "ADDED ... must include at least one scenario". "The explainer degrades gracefully on failure" has two behaviors but only one scenario (D6).
- The main spec has 13 scenarios. The 4 long requirements hold 10 of them, and 21 SHALL statements.
- This branch stacks on `split-long-reqs-pilot` (PR #247). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-pilot`.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement states one behavior in no more than 500 characters. The longest is about 430.
- After archive, the spec holds every one of its 13 scenario blocks word for word, plus the one added on purpose.

**Non-Goals:**

- Reordering requirements inside the main spec.
- Rewording the 3 requirements already under the limit.
- Any change to code, tests, docs or the verdict document.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-verdict-narrative --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=verdict-narrative`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/verdict-narrative/spec.md`. No code reads requirement headings (D2).

## Decisions

1. **Split the failure requirement in two, and add one scenario.** The first behavior is "no narrative, and the entity is actively unavailable". The second is "the verdict is still delivered, and the failure is only logged". The one scenario, "Provider failure does not block the verdict", asserts both. It stays whole under the second, because its name fits that one (epic decision 2). The first gets a new scenario, "A provider timeout yields no narrative", because strict validation needs one. Timeout is an edge case the requirement already names, so the scenario adds no rule (epic decision 4). Existing tests already assert it: `test_a_timeout_yields_none_without_blocking` and `test_a_failing_explainer_still_publishes_the_verdict_and_marks_unavailable`.
   - Alternative: keep one requirement under a new heading, cut to 500 characters. That keeps two behaviors in one requirement, which is what the epic removes.
   - Alternative: add a scenario to the second requirement instead. The existing scenario is named for that behavior, so it would sit under the wrong one.
2. **Split the settings-error requirement by kind of input.** Each of its five scenarios tests one kind: a bad defined setting, an unknown key, a value that is not a mapping, an empty block, and a valid key. So each kind becomes one requirement with its scenario.
   - The general rule says that an error and the log show no value from the block, from any source of settings. Each of the three error requirements states it again, so each reads on its own (plan review round 1, Findings 1 and 2).
   - The three kinds are every way the process rejects the block. `pierpressure/core/config.py` rejects a value that is not a mapping at line 406, and every other fault comes from validating `ExplainerConfig` at line 549: a bad defined value or an unknown key. So stating the rule three times covers what the one general rule covered.
   - The repeats raise the SHALL count from 21 to 24. Nothing new is required.
3. **Keep the cache key with the reuse requirement.** Its scenario, "Identical influencing terms reuse the cached narrative", names every term in the key. The fresh-narrative requirement refers to "any verdict term that influences the narrative", so it reads on its own.
4. **Headings avoid the bare word "provider".** The glossary defines Provider as a weather provider. This spec's text keeps "provider" where it already said it, but new headings say "explainer failure" or "the LLM" instead (D9).
5. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It inserts each named scenario block exactly as the main spec has it, and fails if a name is missing or used twice.
6. **Accept archive's order.** The 11 new requirements land at the end of the spec, after the 3 that stay. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: verdict-narrative: 1 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count SHALL, MUST and MAY in the ADDED requirements: 24 expected, against 21 in the originals (Decision 2). The plan review compared each original with its parts.
- [The added scenario states a rule the spec did not have] → Its WHEN and THEN restate only what "An explainer failure yields no narrative and an unavailable entity" already says for the timeout case. The pull request lists it.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
