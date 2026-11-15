## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, run by `lets delegate review run` through the t3 resolver)
- **Independent**: yes. The author is the claude family. `lets delegate` exited 5 ("the session stopped to ask"), but the reviewer's session completed and its final message holds the full review (T3 thread 3c44811f-bc08-4c30-a662-a5fd98c9a55d).
- **Tool restrictions**: read-only by instruction; the session ran in plan mode
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0041, and the source files `pierpressure/core/config.py`, `addon_options.py`, `addon_settings.py`, `__main__.py`, `core/horizon.py`, `delivery/mqtt.py`, at commit 47ba2d9

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Padded ids behave by digit** (check: Assumption rows, D6). The reader keeps
   the YAML 1.1 patterns, so `id: 07` is a number and fails the id check, while
   `id: 08` stays text and passes. A user who numbers piers with padded digits
   sees `01` to `07` fail and `08` pass. The reviewer also said the spec claims
   every padded integer is decimal, while `080` stays text in the raw mapping.
   Verdict: CONFIRMED in part. The digit split is real but not new: today
   `id: 07` is the number 7 and already fails. The spec clause the reviewer
   quoted was rewritten before this review: it speaks of number settings, which
   take 80 from `080` through the settings check.
2. **Test seams cannot see publishing** (check: Test seams, Scenario
   testability). Several THEN lines say a verdict is or is not published, but
   the named seams return a configuration or raise `ConfigError`.
   Verdict: CONFIRMED as a gap in design.md. The existing tests of "One invalid
   pier does not disable valid piers" already use the loaded `piers` as the
   evidence for a verdict, for example
   `test_form_setup_gives_a_verdict_without_a_file` in `tests/test_main.py`.
   The design did not say so.

### 📌 Suggestions

3. **Numeric repeated ids skip the startup stop** (check: Scope, D8). Two
   entries with `id: 12` and one valid pier start, because the repeat check
   counts only text ids. Verdict: CONFIRMED, declined. A number id fails each
   entry's own check, so both entries are skipped and logged, and neither
   publishes to a shared topic. D8 chose this on purpose.
4. **Long sentences** (check: Plain language). Sentences over 30 words in
   proposal.md, ADR-0041, the night-verdict delta and design.md.
   Verdict: CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD5: the README tells users to quote an id that looks like a
   number, and says why `07` and `08` differ (finding 1).
2. design.md Test Seams: say that a pier in the loaded `piers` is the evidence
   of a verdict, and that a `ConfigError` means startup stops before anything is
   published (finding 2).
3. Split the sentences over 30 words in proposal.md (Why), ADR-0041 (Context),
   the night-verdict delta (the zero-padded requirement) and design.md (the
   leading-zero risk) (finding 4).

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed in part by required change 1. The digit split is YAML 1.1 behavior that
   exists today and that D5 and D6 keep on purpose. Changing it would make
   `id: 08` fail, which ADR-0041 rejects. The quoting advice covers the user.
2. Fixed by required change 2. The spec keeps its THEN lines, which match the
   wording of the existing night-verdict and ha-addon scenarios.
3. Declined: a number id is a per-pier error (D8), and the skipped entries
   publish nothing, so no verdict is overwritten.
4. Fixed by required change 3.
