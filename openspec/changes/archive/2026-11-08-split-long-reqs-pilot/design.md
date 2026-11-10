## Context

- OpenSpec 1.16.0 counts the prose between a `### Requirement:` heading and its first `####` heading, and warns above 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading: validate and archive both fail with "Requirement present in both ADDED and REMOVED" (brainstorm D3).
- Archive deletes a REMOVED requirement and appends ADDED requirements at the end of the main spec. A rehearsal in a throwaway copy showed this.
- Archive does not check that a scenario under a REMOVED requirement comes back under an ADDED one. Epic #230 decision 6 gives a check for that.
- That check passes when it should fail (D10). Its code sits inside a numbered list, so a copy of the raw issue body keeps a 3-space indent, and Python stops with `IndentationError`. A wrong spec path or a wrong working directory makes it fail too. Every failure leaves both sides of `diff` empty, so the check prints nothing, which reads as a pass.
- The local `main` branch in this checkout is stale (`cabb9e3`), while `origin/main` is `a43e36d`, the commit this change branched from. `git merge-base main HEAD` gives the wrong BASE here.

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

- **Primary test seam:** `openspec validate split-long-reqs-pilot --strict` before archive, and the fixed scenario-preservation check (Decision 5) after archive, for both specs.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of two main specs, `openspec/specs/pier-equipment/spec.md` and `openspec/specs/release-image/spec.md`. No code reads requirement headings.

## Decisions

1. **New headings for every ADDED requirement.** Reusing the old heading would keep links to it working, but OpenSpec rejects it (D3). A two-change split, REMOVE first and ADD later, would leave a spec with missing behavior between merges. New headings are the only option that works in one change.
2. **Accept archive's order.** Archive puts the new requirements at the end of each spec. In `pier-equipment`, "Field of view is derived offline from the equipment" then comes first. Editing the main spec by hand after archive would put the equipment requirements back on top. But every later story would need the same manual step. It could also slip a text change past the scenario check. The order carries no meaning, so we keep what archive writes.
3. **Reword only to make a requirement read on its own.** The one edit beyond moving text is in `release-image`: the first new requirement says "This is the version pull request.", and the failure requirement says "the version pull request" where the original said "the pull request". The term already appears in the original's scenarios, so it is not new (epic #230 decision 5).
4. **The REMOVED Reason names every new requirement**, so a reader of the archived change can follow each behavior to its new heading.
5. **Fix the scenario-preservation check, and put the fix in the epic.** The fixed check:
   - compares the scenario blocks as counted sets in Python, and prints each lost block with `<` and each added block with `>`;
   - fails a spec that lost or changed a scenario, or that had no scenarios at BASE, so a failed read or a bad path can no longer look like a pass;
   - passes a spec whose only differences are added scenarios, which epic decision 4 allows, and says to list them in the pull request;
   - prints `OK: <cap>` for each spec that passes, so a pass is a line you can see, not silence;
   - exits non-zero when any spec fails, not only the last one;
   - takes BASE from `git merge-base origin/<target> HEAD`. It runs `git fetch` first, and only warns if the fetch fails, so it still works offline;
   - moves to the repository root itself, and runs in a subshell, so its `exit` cannot close the reader's shell.

   In the epic body, the code block sits at the left margin, outside the numbered list, so a copy of the raw body runs as it is. A story sets `TARGET` and `CAPS` at the top, and runs it from anywhere in its checkout. The check, as tested:

```bash
(
TARGET=main                          # the branch this pull request targets
CAPS="pier-equipment release-image"  # every spec this story changed
compare() { python3 -c 'import re,sys
from collections import Counter
def blocks(t):
    return Counter("\n".join(l.rstrip() for l in b.strip().splitlines()) for b in re.split(r"(?m)^(?=#{2,4} )",t) if b.startswith("#### Scenario:"))
cap=sys.argv[1]
old,new=blocks(sys.stdin.read()),blocks(open(sys.argv[2]).read())
if not old: sys.exit(f"FAIL: {cap}: no scenarios found at BASE")
lost,added=old-new,new-old
for s in sorted(lost.elements()): print("< "+s.replace("\n","\n< "))
for s in sorted(added.elements()): print("> "+s.replace("\n","\n> "))
if lost: sys.exit(f"FAIL: {cap}: {sum(lost.values())} scenario(s) lost or changed")
print(f"OK: {cap}" + (f": {sum(added.values())} scenario(s) added; list them in the pull request" if added else ""))' "$@"; }
cd "$(git rev-parse --show-toplevel)" || exit 1
git fetch -q origin || echo "warning: git fetch failed, so BASE comes from the local origin/$TARGET"
BASE=$(git merge-base "origin/$TARGET" HEAD) || exit 1
fail=0
for cap in $CAPS; do
  git show "$BASE:openspec/specs/$cap/spec.md" | compare "$cap" "openspec/specs/$cap/spec.md" || fail=1
done
exit $fail
)
```

The alternative was to keep the old check and warn readers to dedent it. That leaves a check that passes silently on the next mistake, in 13 more stories.

## Risks / Trade-offs

- [A scenario is copied with a changed line break or word, and archive accepts it] → The deltas copy each scenario block from the main spec with a script, not by hand. The fixed check runs after archive and must print `OK:` for each spec.
- [The fixed check has a flaw of its own] → Before it goes in the epic, test it in each of these cases:
  - the real specs: passes;
  - a scenario deleted from the first spec: fails and shows it;
  - a scenario added: passes and lists it;
  - a spec name that does not exist: fails;
  - the code indented by 3 spaces: fails;
  - `git fetch` fails: warns and passes.
- [A SHALL is dropped while splitting] → Count `SHALL` and `MUST` in each spec before and after archive. pier-equipment's count should stay the same; release-image's count should stay the same.
- [Later stories assume the same heading can be reused] → Record the D3 finding in epic #230 decision 5.
- [Editing the epic body overwrites an edit someone else makes at the same time] → Read the body just before the edit, change only decisions 5 and 6, and diff the result against what was read.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
