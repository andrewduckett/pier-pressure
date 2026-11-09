## Story

#232 split-long-reqs-verdict-narrative — every verdict-narrative requirement states one behavior in 500 characters or fewer.
https://github.com/andrewduckett/pier-pressure/issues/232

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which requirements does this story split? | The 4 that `openspec validate --specs` flags in `verdict-narrative`: "Narrative explains an already-computed verdict", "The explainer degrades gracefully on failure", "Narratives are cached on the deterministic verdict terms" and "An error about the explainer settings shows none of their text". The other 3 are under the limit and stay as they are. | Evidence: #232 body; `openspec validate --specs --json` |
| D2 | Does a change already in flight touch `verdict-narrative`? | No. No open pull request or remote branch changes `openspec/specs/verdict-narrative/`. No code, test, doc or other spec refers to the 4 headings. | Evidence: `gh pr list`; `git diff origin/split-long-reqs-pilot...<branch>` for each remote branch; `grep` of the repository |
| D3 | How does "Narrative explains an already-computed verdict" split? | Into two: the explainer takes only the verdict document as input, and produces prose from its terms; the explainer never computes or changes the verdict. The manual acceptance check stays with the first. | Evidence: `openspec/specs/verdict-narrative/spec.md`, one scenario per behavior |
| D4 | How does "Narratives are cached on the deterministic verdict terms" split? | Into two: the cache key covers every influencing term, and identical terms reuse the cached narrative; any changed term gives a fresh narrative, and the cache never serves stale prose. | Evidence: `openspec/specs/verdict-narrative/spec.md`, one scenario per behavior |
| D5 | How does "An error about the explainer settings shows none of their text" split? | Into five, one per kind of input: a rejected block shows no value, and a bad defined setting is named with its rule; an unknown key is not named, and the defined settings are listed; a value that is not a mapping is reported as such; an empty block disables the explainer; a valid API key is masked and used only for the provider call. "For every source of settings" stays with the general rule in the first. | Evidence: `openspec/specs/verdict-narrative/spec.md`, one scenario per kind of input |
| D6 | How does "The explainer degrades gracefully on failure" split, when it has only one scenario? | Into two: a failed call gives no narrative and an actively unavailable narrative entity; a failure is logged and never blocks, delays or corrupts the verdict. The existing scenario, "Provider failure does not block the verdict", stays whole under the second. The first gets one new scenario for the timeout edge case the requirement already names, so each requirement keeps a scenario. The pull request lists it. | Assumption (the user delegated the brainstorm). Evidence: OpenSpec strict validation rejects an ADDED requirement with no scenario (probe under `.workspace/`); epic #230 decision 4; `tests/test_explainer.py` `test_a_timeout_yields_none_without_blocking` and `tests/test_service_explainer.py` `test_a_failing_explainer_still_publishes_the_verdict_and_marks_unavailable` |
| D7 | Where does each scenario go? | Each of the 10 existing scenarios goes, word for word, under the one new requirement it tests. Only the D6 scenario is added. | Evidence: each scenario's WHEN and THEN in the main spec name one behavior |
| D8 | May the SHALL text be reworded? | Only to make each new requirement read on its own, such as naming its subject again. Every SHALL keeps its meaning. A rule shared by several kinds of input stays in one place. | Evidence: #230 Shared decision 3 |
| D9 | Which words do the new headings use? | The words the spec already uses: explainer, narrative, narrative entity, verdict, the `explainer` block, API key. In this spec "provider" means the LLM provider, not the glossary's weather provider, so headings avoid the bare word. No term is new. | Evidence: `openspec/glossary.md` (Provider, scope: conditions, configuration and provider health); #230 Shared decision 5 |
| D10 | What does "done" mean for this story? | `openspec validate split-long-reqs-verdict-narrative --strict` passes before archive; after archive `verdict-narrative` has no long-requirement warning; the epic's scenario check with `TARGET=split-long-reqs-pilot` and `CAPS=verdict-narrative` prints `OK: verdict-narrative` with 1 scenario added; `mise run check` is green. | Evidence: #230 Shared decisions 6 and 7; the stacked base, PR #247 |

## Changes from the story

None

Confirmed by user: yes
