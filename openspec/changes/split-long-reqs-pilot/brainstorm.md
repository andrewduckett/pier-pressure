## Story

#231 split-long-reqs-pilot — pier-equipment and release-image each state one behavior per requirement, and the split pattern is proven.
https://github.com/andrewduckett/pier-pressure/issues/231

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which requirements does this story split? | Only "Equipment is optional on each pier" (pier-equipment) and "A release proposes the add-on version update" (release-image). Each spec has no other long requirement. | Evidence: #231 body; `openspec validate --specs --json` |
| D2 | Does a change already in flight touch either spec? | No. No open pull request or remote branch changes `openspec/specs/pier-equipment/` or `openspec/specs/release-image/`. | Evidence: `gh pr list`; `git diff origin/main...origin/<branch>` for each branch |
| D3 | Can one delta REMOVE and ADD the same heading? | No. OpenSpec 1.16.0 fails validate and archive with "Requirement present in both ADDED and REMOVED". Every ADDED requirement gets a heading of its own. | Evidence: probe change run in a throwaway copy under `.workspace/` |
| D4 | How does "Equipment is optional on each pier" split? | Into three: the equipment's shape under the `equipment` key; a pier without equipment still gets a verdict and changes no other field; every equipment value is strictly positive. | Evidence: `openspec/specs/pier-equipment/spec.md`, one paragraph of the requirement per behavior |
| D5 | How does "A release proposes the add-on version update" split? | Into four: the release opens a version pull request that changes only the add-on version; the release leaves `main` unchanged; at most one version pull request stays open; a failed pull request fails the run but keeps what was published. | Evidence: `openspec/specs/release-image/spec.md`, one SHALL group of the requirement per behavior, each with its own scenario |
| D6 | Where does each scenario go? | Each of the 9 scenarios goes, word for word, under the one new requirement it tests. The `rig` key scenario goes with the `equipment` key requirement. No scenario is added. | Evidence: each scenario's WHEN and THEN in the two main specs name one behavior |
| D7 | May the SHALL text be reworded? | Only to make each new requirement read on its own, such as naming its subject again. Every SHALL and MUST keeps its meaning. | Evidence: #230 Shared decision 3 |
| D8 | What does "done" mean for this story? | `openspec validate split-long-reqs-pilot --strict` passes before archive; after archive neither spec has a long-requirement warning; the scenario-preservation check (as fixed in D10) passes for both specs; `mise run check` is green. | Evidence: #230 Shared decisions 6 and 7 |
| D9 | Where are the pilot's findings recorded? | The D3 finding goes in decision 5 of the epic #230 body, so later stories use new headings. The D10 fix replaces the check in decision 6. | Evidence: #231 Scope |
| D10 | Does the scenario-preservation check need a fix? | Yes. Copied from the raw issue body, its Python keeps the list's indent and fails, yet the check prints nothing and passes. A wrong spec path also passes. The fixed check stops on any failure or on zero scenarios, and prints `OK: <cap>` only when it passes. | Evidence: the raw-body check run under `.workspace/`, plan review round 1 |

## Changes from the story

None

Confirmed by user: yes
