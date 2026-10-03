## Review Metadata

- **Review round**: 2
- **Prior round**: round 1 (Gemini 3.1 Pro High) returned REVISE: missing OCI index annotations for GHCR linking (critical), undocumented cancellation of a waiting release, and plain-language findings. The author fixed all of them before this round.
- **Reviewer context**: cross-model (Gemini 3.1 Pro High via the `agy` CLI in plan mode), in a fresh context with no authoring transcript
- **Metadata note**: the author corrected the round number and reviewer context above. A prompt edit failed to apply, so the reviewer labelled this output "round 1" and "fresh-context subagent".
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/release-image/spec.md, adr.md, docs/decisions/0013-calver-versions-from-git-tags.md, relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None. The design correctly models the capabilities of `hatch-vcs`, `uv` (`cache-keys`, `required-version`), and `astral-sh/setup-uv`. Workflow concurrency, permissions, and multi-arch OCI label propagation are mechanically sound.

### 🟡 Moderate

1. **Plain Language (Passive Voice)**: In `design.md`, section D3 (One release workflow with two jobs), the bullet "Image first, then tag" states: "The tag and GitHub release are created only after the push succeeds...". This uses passive voice, hiding the actor (the workflow).
2. **Plain Language (Passive Voice)**: In `specs/release-image/spec.md`, section "Requirement: Releases never share a version", the scenario states: "The second release is cancelled without pushing an image or creating a tag". This uses passive voice.
3. **Plain Language (Passive Voice)**: In `specs/release-image/spec.md`, section "Requirement: The commit is tagged and released only after the image is pushed", the requirement states: "After the image is pushed, the release SHALL tag...". This uses passive voice.
4. **Plain Language (Passive Voice)**: In `design.md`, section "Risks / Trade-offs", the first bullet states: "The README is changed in this same change...". This uses passive voice.
5. **Plain Language (Passive Voice)**: In `adr.md`, the review summary states: "D4 (QEMU emulation) can be swapped for native runners...". This uses passive voice.

### 📌 Suggestions

- **Clarify `hatch-vcs` shallow clone behavior**: In `design.md` "Risks / Trade-offs", the document states `hatch-vcs` reads no tags in CI's shallow checkout and therefore reports `0.1.dev1+g...`. While functionally accurate in its outcome, `setuptools_scm` uses a default template (`0.1.devN`) when no tags are found, rather than deriving it from a prior tag. Consider rewording for precision.
- **`latest` tag semantics**: The spec correctly asserts that `latest` follows the newest release. This is mechanically guaranteed *because* releases only happen from `main`, meaning older branches cannot be backported and tagged out of order. Consider explicitly noting this relationship.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Rewrite `design.md` D3 "Image first, then tag" to use active voice (e.g., "The workflow creates the tag...").
2. Rewrite `specs/release-image/spec.md` "Requirement: Releases never share a version" to use active voice (e.g., "A third trigger cancels the second release...").
3. Rewrite `specs/release-image/spec.md` "Requirement: The commit is tagged and released only after the image is pushed" to use active voice (e.g., "After it pushes the image...").
4. Rewrite `design.md` "Risks / Trade-offs" bullet regarding the README to use active voice (e.g., "This change updates the README...").
5. Rewrite `adr.md` D4 bullet to use active voice (e.g., "The maintainer can swap QEMU emulation...").

CHANGES_APPLIED: yes

## Rebuttals

Required changes 1 to 5: fixed. The reviewer re-checked each item in a separate
read-only pass and reported `RECHECK: ALL APPLIED`.

Moderate findings 1 to 5: fixed. They are the same items as required changes
1 to 5.

Suggestions, declined by the author:

- **`hatch-vcs` in a shallow clone.** The design already says that `hatch-vcs`
  "reads no tags" and gives the resulting `0.1.dev1+g…` form. That matches the
  reviewer's description of the default template, so no rewording is needed.
- **`latest` semantics.** The design's D3 already ties `latest` to releases that
  run only from the newest commit on `main`. Repeating it in the spec would add a
  rationale, not a requirement.

## Process note

In round 2 the reviewer wrote a helper script (`check_prose.py`) at the
repository root, which breaks the read-only constraint. The script only counted
sentence lengths. It changed no artifact, and the author deleted it. The re-check
pass ran under a stricter prompt and wrote no files.


