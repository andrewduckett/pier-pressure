## Story

#234 split-long-reqs-horizon-mask — every horizon-mask requirement states one behavior in 500 characters or fewer.
https://github.com/andrewduckett/pier-pressure/issues/234

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which requirements does this story split? | The 5 that `openspec validate --specs` flags in `horizon-mask`: "Canonical horizon representation", "Inline points configuration", "NINA horizon import", "Flat floor and default open sky" and "The horizon does not change the verdict document". "Terrain-clearance query" and "Unsupported formats fail clearly" are under the limit and stay as they are. | Evidence: #234 body; `openspec validate --specs --json` |
| D2 | Does a change already in flight touch `horizon-mask`? | No. No open pull request or remote change branch edits `openspec/specs/horizon-mask/`. `origin/assets` differs only because it shares no history with `main`. | Evidence: `gh pr list`; `git diff origin/main...<branch> -- openspec/specs/horizon-mask` for each remote branch |
| D3 | How many scenarios may this story add? | Only where a split-out behavior would otherwise have no scenario, since strict validation rejects an ADDED requirement without one. Each added scenario restates a SHALL the requirement keeps, and an existing test already asserts it. The pull request lists each one. | Assumption (the user delegated the brainstorm). Evidence: #233 brainstorm D3; #230 Shared decision 4 |
| D4 | How does "Canonical horizon representation" split? | Into six: the samples and the azimuth and altitude conventions; every horizon source gives that representation; interpolation round the closed ring; sparse samples and low anchor samples; a single-sample horizon is flat; the fixed altitude precision. The sentence on sub-precision noise in repeated azimuths moves to the repeated-azimuth requirement (D5), which it governs. The first two each get one added scenario, backed by `tests/test_horizon.py` `test_azimuth_360_normalizes_to_zero_and_deduplicates` and `test_nina_fixture_imports_to_the_equivalent_inline_points_horizon`. | Assumption. Evidence: `openspec/specs/horizon-mask/spec.md`; `tests/test_horizon.py` |
| D5 | How does "Inline points configuration" split? | Into six: an inline list in any order; the azimuth and altitude ranges; repeated azimuths; at least one pair; points written as YAML text; text that cannot give a list is rejected with an error that names `horizon.points`. The two repeated-azimuth scenarios go together. "At least one pair" gets one added scenario, backed by `tests/test_horizon.py` `test_at_least_one_point_is_required`. | Assumption. Evidence: `openspec/specs/horizon-mask/spec.md`; `pierpressure/core/config.py` (an empty list reaches `from_points`) |
| D6 | How does "NINA horizon import" split? | Into five, one per SHALL group: parsing the pair-per-line text; blank and comment lines; the 360 and below-0 quirks; malformed content; relative file references. Each keeps the one scenario that tests it. No scenario is added. | Evidence: each scenario's WHEN and THEN in the main spec |
| D7 | How does "Flat floor and default open sky" split? | Into three: a flat floor; no horizon means flat open sky; only one horizon source per pier. Each keeps its one scenario. | Evidence: `openspec/specs/horizon-mask/spec.md`, one scenario per behavior |
| D8 | How does "The horizon does not change the verdict document" change? | It states one behavior and is 3 characters over the limit. It is REMOVED and ADDED once, under a new heading, with tighter wording and the same SHALL statements and scenario. | Assumption. Evidence: #230 Shared decisions 1 and 5 |
| D9 | The requirement in D8 says `targets` stays empty, but `tests/test_horizon_contract.py` and `target-ranking` say the horizon now changes `targets`. Does this story fix that? | No. The epic changes no behavior and no meaning (Shared decision 3), so the new requirement keeps the old meaning. The drift is reported in the pull request for a separate bug. | Assumption. Evidence: `tests/test_horizon_contract.py`; `openspec/specs/target-ranking/spec.md`; #230 Won't |
| D10 | May the SHALL text be reworded? | Only so that each new requirement reads on its own, such as naming its subject again. Every SHALL and MAY keeps its meaning. | Evidence: #230 Shared decision 3 |
| D11 | Which words do the new headings use? | The words the spec already uses: horizon, sample, azimuth, altitude, inline points, flat floor, open sky, horizon source, NINA `.hrz` export and verdict document. The glossary defines none of them, and no term is new. No heading repeats a heading the delta removes or one the spec keeps. | Evidence: `openspec/glossary.md`; `openspec/specs/horizon-mask/spec.md` headings; #230 Shared decision 5 |
| D12 | What does "done" mean for this story? | `openspec validate split-long-reqs-horizon-mask --strict` passes before archive; after archive `horizon-mask` has no long-requirement warning; the epic's check with `TARGET=split-long-reqs-night-card` and `CAPS=horizon-mask` prints `OK: horizon-mask` with 3 scenarios added; `mise run check` is green. | Evidence: #230 Shared decisions 6 and 7; the stacked base, PR #249 |

## Changes from the story

None

Confirmed by user: yes
