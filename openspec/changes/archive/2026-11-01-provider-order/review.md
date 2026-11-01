## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, effort high; the first attempt on gemini/gemini-4-argon returned only a usage-quota message and no review)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0027, relevant source files, at commit `30157d8`
- **Prompt**: `.workspace/provider-order-review-prompt.md`; raw findings in `.workspace/provider-order-review-raw.md`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Golden harness call site** (test seams). `assemble_snapshot` gains a new signature, but `tests/test_golden_verdict.py:108` calls it with two positional forecasts, and the design listed the golden suite as reused without saying its helper changes. CONFIRMED.
2. **Scoring's atmosphere functions take `SecondaryHour`** (contradiction with design D5). `_optional_term`, `optional_term_mean`, `_hour_atmosphere`, `atmosphere_mean` and `_ATMOSPHERE_TERMS` in `pierpressure/core/scoring.py` (lines 190 to 266 and 640) unpack `SecondaryHour`, so "nothing else in scoring changes" was false once that type is removed. CONFIRMED.
3. **Delta headings keep "field" and "source"** (domain language, brainstorm D6). The requirement headings "Availability is stamped per field" and "Entry values carry each source's reading for the hour", and some scenario names, kept the old words. CONFIRMED in part: the two requirement headings are fixed. The scenario names inside the remaining MODIFIED blocks stay, because `openspec validate --strict` refuses a MODIFIED block whose scenario names differ from the main spec's (an earlier validation run in this change reported exactly that for renamed scenarios). Archive carries the body text, which uses the agreed words.

### 📌 Suggestions

4. **Variable count wording** in design D1 ("sixteen keys minus time and the altitudes") could read as sixteen variables; there are thirteen. CONFIRMED.
5. **Sentences over 30 words** in proposal.md, design.md, ADR-0027 and the new spec text. CONFIRMED in part: the reviewer's count joined bullet lists into one sentence in several places; the genuinely long sentences in prose this change wrote are split. Sentences copied unchanged from the main spec into MODIFIED blocks are left as they are, to keep those deltas wording-neutral.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md Test Seams: say that the golden suite's `_verdict_json` helper passes `[(open_meteo_spec, base), (seven_timer_spec, secondary)]` to the new `assemble_snapshot`, and that the expected JSON files do not change.
2. design.md D5: say that the atmosphere functions read `value_at("seeing", slot)` and `value_at("transparency", slot)` directly so `SecondaryHour` can go, with no formula change.
3. Spec deltas: replace the headings "Availability is stamped per field" and "Entry values carry each source's reading for the hour" with "per variable" and "each series' reading", as REMOVED plus ADDED so archive can apply them.
4. design.md D1: state thirteen variable keys, the sixteen timeline entry keys without `time`, `sun_altitude` and `moon_altitude`.
5. Split the long sentences this change wrote in proposal.md, design.md, ADR-0027 and the new spec text.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md Test Seams, "Existing seams reused", in commit `docs: apply plan review changes to provider-order (#146)`.
2. Fixed: design.md D5 now names the five atmosphere functions and the direct reads, same commit.
3. Fixed in part: `specs/conditions/spec.md` now has ADDED "Availability is stamped per variable" and REMOVED "Availability is stamped per field"; `specs/night-verdict/spec.md` has ADDED "Entry values carry each series' reading for the hour" and REMOVED the "each source's" one. Rebutted for scenario names inside MODIFIED blocks: the validator requires them to match the main spec, as recorded above.
4. Fixed: design.md D1 wording, same commit.
5. Fixed for prose this change wrote: proposal.md (the config bullet), design.md (Test Seams, D1 and D2 alternatives, D3 fill rule), ADR-0027 Context, the new conditions and night-verdict requirement text. Declined for sentences copied unchanged from the main spec.
