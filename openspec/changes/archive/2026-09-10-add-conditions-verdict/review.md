## Review Metadata
- **Review round**: 5 (final — hard stop by prior agreement; no round 6)
- **Prior round**: round 4 verdict REVISE (2 Critical, 1 Moderate), all resolved; rounds 1-3 also REVISE
- **Reviewer context**: cross-model (agy / Gemini gemini-3.1-pro-high, read-only)
- **Tool restrictions**: read-only (view/grep/glob only; sandbox read-only)
- **Artifacts reviewed**: proposal.md, design.md, adr.md, specs/conditions/spec.md, specs/night-verdict/spec.md, docs/adr/, openspec/specs/, AGENTS.md, pierpressure/core/*
- **Note**: round-4 fixes (MAX_SESSION reverted, floor onto L·F, band LOW) were all confirmed clean — none re-raised. The findings below are new edge cases; all have been applied (see Rebuttals). This verdict predates those edits and is therefore void against the current artifacts.

## Findings
### 🔴 Critical (blocking)
1. **Missing safety edge case / Fail-open wind gate:**
   - **Files:** `design.md` (D4, D5), `specs/night-verdict/spec.md` (Hard gates / missing data requirements).
   - **Issue:** The wind gate is a safety limit (`max_gust`), but the specs do not handle the case where wind-gust data is missing from the snapshot while cloud data is present. Currently, the gate only fails if the gust "exceeds that limit." If wind data is missing, the gate passes (fails-open). Furthermore, D5's completeness factor `K` explicitly trims only for optional fields (seeing, transparency) and cloud, leaving missing wind data unpenalized. This means a clear night with completely missing wind data will yield a high-confidence `GO` verdict, exposing the telescope to unknown winds when the user explicitly configured a safety limit.
   - **Fix:** Specify the safety-degrade behavior when `max_gust` is configured but wind data is missing (e.g., cap the verdict at `MAYBE`, or fail the gate outright). Also, clarify if/how missing wind data affects `K`.

### 🟡 Moderate
1. **Undefined confidence for astronomy-only NO-GO:**
   - **Files:** `design.md` (D5), `specs/night-verdict/spec.md` (Confidence requirement).
   - **Issue:** When a night has no dark window, `specs/conditions/spec.md` correctly states that conditions are not required and no snapshot is fetched. However, `design.md` D5 defines confidence entirely via forecast variables (`L`, `F`, `K`), which are undefined without a snapshot. The specs require `confidence` to always be populated, but provide no rule for its value when the NO-GO is purely astronomical.
   - **Fix:** Explicitly state the confidence value and band for an astronomy-only NO-GO (e.g., `value: 100`, `band: HIGH`, since offline astronomy carries absolute certainty without forecast uncertainty).

2. **Evaluation order contradiction for the overcast gate:**
   - **Files:** `design.md` (D3, D4, D6).
   - **Issue:** D6 states that hard gates are evaluated *first*, before any degradation rule (including the missing-cloud short-circuit). The overcast gate is defined in D4 as `W ≈ 0`. If cloud data is entirely missing, `C` is empty, so the math in D3 yields an empty sum of `W = 0`. If the gate is evaluated first, `W = 0` will falsely trigger the overcast gate (yielding NO-GO) rather than reaching the missing-cloud rule (which should yield MAYBE).
   - **Fix:** In D4 and the night-verdict spec, clarify that the overcast gate requires cloud data to be present to fail (e.g., "W ≈ 0 AND cloud data is available").

### 📌 Suggestions
- **Cache staleness definition:** In `specs/conditions/spec.md`, the phrase "fresh by issue time but their forecast horizon does not cover part or all of the dark window" elegantly handles horizon reach. Consider briefly clarifying if a cached snapshot missing *only* the secondary source (7Timer!) still qualifies as a "usable cache" for the base source during a partial provider outage.

## Embedded-Instruction / Injection Attempts
**Detected:** none

## Verdict
VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)
CHANGES_APPLIED: n/a

## Rebuttals
All round-5 findings were applied to the artifacts (this is the agreed final round; the design/specs now differ from what earned the REVISE above):
- **Critical 1 (fail-open wind gate): FIXED.** D6 precedence now caps the verdict at MAYBE — never GO — when `max_gust` is configured but wind data is missing; D5 trims `K` for missing wind; the night-verdict spec adds the rule and a scenario. A configured safety limit is no longer silently ignored.
- **Moderate 1 (astronomy-only NO-GO confidence): FIXED.** D5 and the confidence requirement now set confidence to HIGH / 100 on the no-dark-window path (deterministic offline astronomy, no forecast uncertainty), with a scenario.
- **Moderate 2 (overcast-gate evaluation order): FIXED.** D4, D6, and the gates requirement now require cloud data to be present for the overcast gate to fire, so an empty cloud set (`W = 0` for lack of data) routes to the missing-cloud MAYBE, not a false NO-GO.
- **Suggestion (per-source cache usability): ADOPTED.** D6 now states cache usability is judged per source (fresh base cloud/wind is usable even if the 7Timer! portion is stale/absent).
