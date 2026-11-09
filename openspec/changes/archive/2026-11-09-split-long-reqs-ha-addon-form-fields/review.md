## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported a clean working tree after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 269f922

## Findings

### 🔴 Critical (blocking)

1. **"A horizon value beside a set horizon field skips the form pier" and "An equipment value beside an equipment field skips the form pier" drop the rule that the logged error names the pier.** The original said "A pier whose horizon fails these rules SHALL be skipped with a logged error that names the pier" for all its cases, the mapping case included, and its equipment twin said the same. The two new requirements said only "The pier SHALL be skipped". Check: **CONFIRMED, fixed** by required change 1.

### 🟡 Moderate

2. **"Skipping every form pier for its horizon, equipment or gates stops the add-on" narrows the stop rule to three causes.** The originals each said "When every pier is skipped, the add-on SHALL stop", with no cause. A form whose two piers fail, one for its latitude and one for its horizon, would fall outside the new wording. Check: **CONFIRMED, fixed** by required change 2.

### 📌 Suggestions

3. **Nine ADDED requirements have sentences over 30 words**, mostly from the scope prefix and the full title of a pointed-to requirement. Check: **CONFIRMED, declined.** The text stays as close to the original as each requirement allows, so its meaning cannot drift (D13), and a pointer must quote its target's full heading to be found.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In the two requirements for a `horizon` or `equipment` value beside a set field, replace "The error SHALL name each of those fields. The pier SHALL be skipped, and the other piers SHALL still be published." with "The pier SHALL be skipped with a logged error that names the pier and each of those fields. The other piers SHALL still be published." Update design.md Decision 4 and the expected count: 52 normative words, 3 of them SHALL NOT.
2. Rename the shared stop requirement to "Skipping every pier on the Configuration form stops the add-on", and drop its list of causes: "Inside an add-on, when the service skips every pier on the Configuration form, the add-on SHALL stop with a configuration error, as it does for any setup with no valid pier." Update the three REMOVED Reasons, design.md Decisions 1 and 2 and its Risks, and ledger row D7.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1. Both requirements are now 468 and 471 characters.
2. Fixed: required change 2.
3. Declined: wording stays close to the original so the meaning cannot drift (D13).
