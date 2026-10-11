## Review Metadata

- **Review round**: 2
- **Prior round**: Round 1 — VERDICT: REVISE. A ranking scenario could not hold for targets of unknown size; D3 wrongly said the core rejects wrong-type values; manual-check and rollback claims were unverified; zero and negative coverage was thin; the ADR manifest had a recap. The author revised all of these.
- **Reviewer context**: cross-model (GPT, `gpt-6-sol` via `codex exec`, reasoning effort medium)
- **Tool restrictions**: read-only sandbox (`codex exec -s read-only`)
- **Artifacts reviewed**: proposal.md, design.md, adr.md, specs/ha-addon/spec.md, and relevant source files

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

- **Delta spec, “Equipment from the form ranks like file equipment” (lines 112–119):** The scenario requires identical *verdict documents* but matches only location and three equipment values. The document contains the pier ID, and a different reducer, horizon, elevation, or other pier setting can change the result. As written, a valid implementation could fail this test. Specify identical pier IDs and all other inputs, including reducer, horizon, evaluation instant, and conditions. Use a target with known catalog size and assert that its field-of-view term contributes; otherwise the ranking check can pass without exercising equipment.

### 🟡 Moderate

- **Delta spec, “A value of 0 or less skips only its pier” (lines 138–148):** The examples cover zero focal length and a negative reducer, but neither sensor dimension. The requirement applies to all four fields. Add parameterized checks for zero and negative values for each field, asserting the skipped pier, logged field path, and continued publication for a valid pier.
- **Design, D3 (lines 93–98):** `null` is defined as unset, but no scenario checks it. Add cases for all four fields being `null` and for a required field being `null` while other equipment fields are set. The former should leave the pier without equipment; the latter should skip it and name the missing field.
- **Design, manual check (lines 146–154):** This is a proposed live check, not evidence that the form behaves as described. Keep it as an explicit verification task with a recorded Supervisor version and result. The proposed `float(0,)?` syntax and omission from `options` agree with [Home Assistant’s schema documentation](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/apps/configuration.md), but the repository’s manifest tests alone cannot verify clearing and saving in the live form.

### 📌 Suggestions

- **Proposal, Why (lines 3–9):** “a worse target list” overstates the effect: the ranking code omits the field-of-view term when an object’s size is unknown. Say that form users cannot get equipment-based ranking for targets with known size.
- **ADR manifest, “Review Summary” (lines 8–22):** The explanation repeats D1 and D2 from the design. Shorten it to the decision that no new ADR is needed and a reference to ADR-0020. This makes the review outcome easier to find. I found no sentence over 30 words or passive construction that hides a necessary actor in the revised change artifacts.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE
## Required Changes (if APPROVE WITH CHANGES)

None. The verdict is REVISE.

CHANGES_APPLIED: n/a

## Rebuttals

Two consecutive REVISE rounds. The review is escalated to the user before a
third round.
