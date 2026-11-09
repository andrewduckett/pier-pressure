## Context

- OpenSpec 1.16.0 counts the prose between a `### Requirement:` heading and its first `####` heading, and warns above 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading: validate and archive both fail with "Requirement present in both ADDED and REMOVED" (brainstorm D3).
- Archive deletes a REMOVED requirement and appends ADDED requirements at the end of the main spec. A rehearsal in a throwaway copy showed this.
- Archive does not check that a scenario under a REMOVED requirement comes back under an ADDED one. Epic #230 decision 6 gives a check for that.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement in both specs states one behavior in no more than 500 characters.
- After archive, both specs hold the same 9 scenario blocks as before, word for word.
- Later stories can copy the pattern as it is.

**Non-Goals:**

- Reordering requirements inside a main spec.
- Any change to code, tests, the verdict document or the release workflow.
- Rewording any requirement already under the limit.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check script.

- **Primary test seam:** `openspec validate split-long-reqs-pilot --strict` before archive, and the scenario-preservation check (epic #230 decision 6) after archive, with `BASE=$(git merge-base main HEAD)`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of two main specs, `openspec/specs/pier-equipment/spec.md` and `openspec/specs/release-image/spec.md`. No code reads requirement headings.

## Decisions

1. **New headings for every ADDED requirement.** Reusing the old heading would keep links to it working, but OpenSpec rejects it (D3). A two-change split, REMOVE first and ADD later, would leave a spec with missing behavior between merges. New headings are the only option that works in one change.
2. **Accept archive's order.** Archive puts the new requirements at the end of each spec. In `pier-equipment`, "Field of view is derived offline from the equipment" then comes first. Editing the main spec by hand after archive would put the equipment requirements back on top, but it adds a manual step each later story would also need, and it could slip a text change past the scenario check. The order carries no meaning, so we keep what archive writes.
3. **Reword only to make a requirement read on its own.** The one edit beyond moving text is in `release-image`: the first new requirement says "This is the version pull request.", and the failure requirement says "the version pull request" where the original said "the pull request". The term already appears in the original's scenarios, so it is not new (epic #230 decision 5).
4. **The REMOVED Reason names every new requirement**, so a reader of the archived change can follow each behavior to its new heading.

## Risks / Trade-offs

- [A scenario is copied with a changed line break or word, and archive accepts it] → The deltas copy each scenario block from the main spec with a script, not by hand. The scenario-preservation check runs after archive and must print nothing.
- [A SHALL is dropped while splitting] → Count `SHALL` and `MUST` in each spec before and after archive. pier-equipment's count should stay the same; release-image's count should stay the same.
- [Later stories assume the same heading can be reused] → Record the D3 finding in epic #230 decision 5.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
