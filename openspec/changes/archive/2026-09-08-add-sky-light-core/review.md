## Review Metadata

- **Review round**: 4
- **Prior round**: round 3 — VERDICT: REVISE (2 Critical: JSON round-trip from serializer-only truncation; UTC-day anchor snapping at longitude 0. 2 Moderate: proposal declaring a unilateral exception to the contract rule; "strictly before" broken by grazing night. 2 Suggestions: octant wrap-around; float-boundary drift. All addressed, incl. amending the config.yaml contract rule.)
- **Reviewer context**: cross-model (agy / Gemini, gemini-3.1-pro-high), read-only `--mode plan`
- **Tool restrictions**: read-only (view/grep/glob); reviewer's only write is its own analysis
- **Artifacts reviewed**: proposal.md, design.md, specs/night-verdict/spec.md, openspec/specs/night-verdict/spec.md, docs/adr/0001–0004, openspec/config.yaml, docs/roadmap.md, pierpressure/core/*.py

<!-- STALENESS: the round-4 fixes below were applied AFTER this verdict, voiding it. -->
<!-- M2-scope (alt/az engine) is escalated to the owner and unresolved. -->

## Findings

### 🔴 Critical (blocking)

1. **Moon horizon altitude threshold underspecified** — `spec.md` (Moon requirement), `design.md` D4. Moonrise/set/above-horizon depends on the altitude boundary (geometric 0° vs ~−0.83° with refraction+radius); unpinned it undermines determinism. **Fixed:** pinned to the moon's geometric centre at 0° altitude (no refraction/radius) in both spec and design.

### 🟡 Moderate

1. **Scope creep / YAGNI: internal alt/az engine has no M2 consumer** — `design.md` D5, `proposal.md`. `sample_altaz` is built and tested in M2 but not called (targets stays `[]` until M5), so it is dead code until M5 may redefine its shape. **ESCALATED TO OWNER — it is a roadmap scope decision (the roadmap lists "target alt/az" under M2).**

2. **Solar-transit anchor is singular at the exact poles** — `design.md` D1a. `PierConfig` permits `abs(latitude) == 90`, where the sun does not transit a meridian, breaking the continuous-night solar-day anchor. **Fixed:** anchor falls back to the UTC calendar day at the poles.

### 📌 Suggestions

1. **Phase angle must be taken mod 360°** — `design.md` D4. Bare longitude subtraction can go negative and miss the octant checks. **Fixed (noted in D4).**

2. **`Moon` model's `rise`/`set` need the shared aware-UTC/truncation validator** — `design.md`. **Fixed:** D4 now requires the same `@field_validator` → `_require_aware_utc` (with `microsecond=0`) that `DarkWindow` uses.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)

n/a — verdict is REVISE.

CHANGES_APPLIED: n/a

## Rebuttals

- **C1, M2, S1, S2** — accepted and fixed (details above); these void the round-4 verdict.
- **M1 (alt/az scope)** — RESOLVED by the owner: the target alt/az night-grid engine is **deferred to M5** (where it has a ranking consumer), removing the dead-code/YAGNI concern. Trimmed from the proposal and design D5; the roadmap now lists alt/az under M5. M2's scope is now exactly sun (`dark_window`) + moon.

## Escalation & Disposition

Four consecutive REVISE rounds; findings narrowed steadily from fundamental design gaps (rounds 1–2) to determinism pins and edge cases (rounds 3–4), with no repeats — the reviewer earned its keep, but by round 4 was surfacing diminishing micro-findings rather than blockers. **All round-4 findings are now resolved** (C1/M2/S1/S2 fixed; M1 scope decided). The owner's plan was "one confirming round 4, then tasks," and the owner directed proceeding to tasks without a further round. This round-4 REVISE verdict is therefore stale (the artifacts were revised after it), and work proceeds to tasks under that explicit direction rather than looping for a machine-readable APPROVE that an indefinitely-adversarial reviewer may withhold over ever-finer nits.
