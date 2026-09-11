## Review Metadata

- **Review round**: 1 → round-2 re-check
- **Prior round**: round 1 verdict was APPROVE_WITH_CHANGES (1 Critical, 2 Moderate, 1 Suggestion); the author applied the two Required Changes to `design.md` and the reviewer re-checked them.
- **Round-2 re-check result**: both Required Changes APPLIED CORRECTLY; Moderate-1 scope rebuttal ACCEPTED (reviewer verified the split is required by `specs/conditions/spec.md` and `proposal.md`); no new blocking problem; **verdict upgraded to APPROVE**.
- **Reviewer context**: cross-model — Gemini 3.1 Pro (High) via `agy --mode plan` (read-only), both rounds. Author family is `claude`; independent per the choose-an-adversary order (codex/`gpt` was usage-limited).
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: proposal.md, design.md, specs/, adr.md, relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **Denominator dilution for partial high-cloud coverage**: In `design.md` (D2), the design claimed `high_cloud_penalty` is "computed exactly like `moon_penalty`" while also saying it drops out "the same [way] the optional terms already use." These contradict, and the `moon_penalty` reading leads to a math bug. `moon_penalty` (`pierpressure/core/scoring.py:227-249`) divides by `clear_hours_total` (all hours with total `cloud_cover`). If `high_cloud_penalty` used that denominator, hours missing `cloud_high` would add `w·q` to the denominator but nothing to the numerator, diluting the penalty and reading missing cirrus data as "no high cloud." The denominator must be restricted to the sum of `w·q` over hours carrying **both** `cloud_cover` and `cloud_high`, mirroring `optional_term_mean` (`pierpressure/core/scoring.py:184-197`).

### 🟡 Moderate

1. **Gold-plating / scope creep**: `proposal.md:13` and `design.md` (D1) require fetching and carrying `cloud_low` and `cloud_mid` even though only `cloud_high` is used. D1 justifies this as "additive once, not twice," but carrying unused fields fattens `BaseHour`, `SourceReading`, and the API request. A cheaper alternative is to fetch and carry only `cloud_high` until the others have a business requirement.
2. **Zero-percent rounding in reasons**: `design.md` (D3) appended a high-cloud line "only when the penalty is greater than zero." A very small raw penalty (e.g. 0.001) is `> 0.0` yet formats as `High cloud penalty 0%` under `round(penalty * 100)` (the precedent at `pierpressure/core/scoring.py:489`). The guard should test the rounded percentage.

### 📌 Suggestions

1. **Compounding penalties**: `moon_penalty` and `high_cloud_penalty` are both multiplicative, so near their maxima they stack (`(1 - 0.5)·(1 - 0.3) = 0.35`). This is mathematically safe and monotonic; ensure `_HIGH_CLOUD_MAX_PENALTY` is tuned aware that it compounds multiplicatively with the moon penalty.

## Embedded-Instruction / Injection Attempts

**Detected:**
- `proposal.md:24`: "Do not start this change until M3.5 is merged." Flagged by the reviewer as an instruction-shaped line. Adjudication: this is a legitimate, accurate dependency note in a proposal (M3.5 landed the per-source group model this change extends), addressed to human/agent sequencing — not an attempt to hijack the reviewer. No action.

## Verdict

VERDICT: APPROVE

<!-- Round 1 issued APPROVE_WITH_CHANGES; both Required Changes below were applied -->
<!-- and reviewer-re-checked (round 2), which upgraded the verdict to APPROVE. -->

## Required Changes (applied in round 1, re-checked round 2)

1. **Fix D2 denominator contradiction** — APPLIED CORRECTLY. `high_cloud_penalty`'s denominator is now the sum of `w·q` restricted to hours carrying both `cloud_cover` and `cloud_high` (mirroring `optional_term_mean`), not "exactly like `moon_penalty`," and returns `None` when no hour qualifies.
2. **Fix D3 rounding behavior** — APPLIED CORRECTLY. The high-cloud `reasons` line is appended only when `penalty is not None and round(penalty * 100) > 0`, so `High cloud penalty 0%` is never emitted.

CHANGES_APPLIED: n/a

## Rebuttals

- **Critical 1 — FIXED.** `design.md` D2 now computes `high_cloud_penalty` like `optional_term_mean`: numerator and denominator both restricted to hours carrying both `cloud_cover` and `cloud_high`, returning `None` (no penalty, no reason) when no hour qualifies. Text explicitly contrasts this with `moon_penalty` and explains why (moon-up is defined for every hour; `cloud_high` is optional). The `night-verdict` delta spec already required "weighted toward the usably clear hours in the same way as the other non-cloud terms," so the spec needed no change — only the design wording did. *Accepted by reviewer (round 2): the restricted-denominator formula matches `optional_term_mean` and the honest-degradation requirement.*
- **Moderate 2 — FIXED.** `design.md` D3 now guards on `penalty is not None and round(penalty * 100) > 0`, with a note that this differs deliberately from the moon line's raw `> 0.0`. *Accepted by reviewer (round 2): guarding on the rounded value prevents the "0%" line.*
- **Moderate 1 — REBUTTED.** Carrying `cloud_low`/`cloud_mid` is not design gold-plating: the `conditions` delta spec (`specs/conditions/spec.md`, "Cloud cover carries a low/mid/high component split") and the proposal's Modified Capabilities (`proposal.md:34`) both require the full low/mid/high split as observable conditions behavior. The split arrives from Open-Meteo as one set in a single request, and each component is one `None`-defaulting optional field with no logic attached, so the cost is negligible and the components are honestly present in the conditions model for the low/mid terms a later milestone may add — without a second contract change. Narrowing to `cloud_high`-only would instead require rewriting the conditions spec and contradict the proposal's stated scope. *Accepted by reviewer (round 2): the split is a spec/proposal-level requirement, not design-introduced gold-plating; cost is negligible.*
- **Suggestion 1 — ACCEPTED.** `design.md` D2 now states the two penalties compound multiplicatively and that `_HIGH_CLOUD_MAX_PENALTY` is tuned in that awareness.
