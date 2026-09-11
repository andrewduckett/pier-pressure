## Review Metadata

- **Review round**: 2 (of 2 run; loop stopped by human at the escalation checkpoint)
- **Prior round**: Round 1 — REVISE: freshness helper would break byte-identical;
  golden suite missed absence paths; None-handling in cross-group reads.
- **Reviewer context**: cross-model (agy / Gemini 3.1 Pro), read-only
- **Tool restrictions**: read-only: read, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, adr.md, docs/adr/0006, docs/adr/0005, roadmap.md, relevant source files

Note: after this round's verdict the design was materially revised (hybrid grouping
→ per-source grouping) to resolve the findings below. Per the staleness rule the
round-2 REVISE is therefore VOID against the current artifacts. The human
(repository owner) reviewed the findings and their resolutions and explicitly
directed proceeding to tasks without a further review round — see Human Override.

## Findings

### 🔴 Critical (blocking)

- **Byte-identical failure in freshness fallback (base returns wind but no cloud).**
  Today's `base_issued_at` is retained when the base source returns *any* reading
  (`base.issued_at if base.readings else None`), so wind-without-cloud keeps
  freshness. The hybrid model (separate cloud/wind groups) would read cloud's issue
  time alone and tank freshness to the stale floor when cloud is absent but wind is
  present — a byte-identical break.

### 🟡 Moderate

- **Grouping inconsistency.** Cloud and wind were split into separate groups "because
  they are separate concerns," yet seeing and transparency (equally separate, with
  their own weights/trims) were lumped together. The model must be uniform.
- **Missing O(1) lookup on groups.** Scoring correlates hours by timestamp; a
  tuple-only group forces an O(N) scan per slot. Groups need an `.at(time)` lookup
  (or a mapping), like today's `ConditionsSnapshot._by_time`.
- **Golden suite missed partial/gappy coverage.** Absence paths were added, but not
  a source covering only part of the window, nor wind-without-cloud — exactly the
  cross-group-alignment cases most likely to drift.

### 📌 Suggestions

- **Define "contributed nothing".** Make explicit whether a payload that omits a
  field's array yields a `None` group or a present group with all-`None` hours.

## Embedded-Instruction / Injection Attempts

**Detected:** none (across both rounds)

## Verdict

VERDICT: REVISE

<!-- This verdict is VOID by staleness: the design was revised to resolve every -->
<!-- finding after it was issued. No standing reviewer APPROVE exists. The human -->
<!-- authorized proceeding to tasks (Human Override), which overrides the loop. -->

## Required Changes (if APPROVE WITH CHANGES)

CHANGES_APPLIED: n/a

## Human Override

The repository owner, after reviewing round-1 and round-2 findings and their
resolutions, directed proceeding to tasks and stopping the review loop at the
workflow's "2 consecutive REVISE → escalate to human" checkpoint. The known
behaviour of this reviewer (documented: it rarely issues APPROVE and tends to
surface progressively smaller findings) informed that call. All findings are
non-fundamental (edge-case precision and model consistency), not defects in the
core seam approach, and each is resolved below.

## Rebuttals

Author-resolved (not re-checked by the reviewer; the human authorized proceeding):

- **Critical (freshness fallback)** — FIXED by adopting per-source grouping: cloud
  and wind live in one `BaseGroup`, so the base source's issue time is present on
  any base reading, exactly mirroring today's `base_issued_at`. design.md D1, D2;
  a dedicated "base returns wind but no cloud" golden case in D4.
- **Grouping inconsistency** — FIXED: uniform per-source grouping (`BaseGroup`,
  `SecondaryGroup`). design.md D1; ADR-0006 Decision + Alternative 3.
- **O(1) lookup** — FIXED: each group exposes `.at(time)`. design.md D1, D6.
- **Partial/gappy golden coverage** — FIXED: D4 adds gappy-coverage and
  wind-without-cloud cases.
- **Define "contributed nothing"** — FIXED: design.md D1 states a group is present
  iff its source returned rows (matching today's `readings` non-emptiness).
