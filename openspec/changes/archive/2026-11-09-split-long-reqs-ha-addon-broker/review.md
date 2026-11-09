## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (`gemini/gemini-3.8-flash` through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree stayed clean (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `9f2b64a`
- **Effort**: low, from design.md's scrutiny tier

The reviewer checked meaning, scenario placement and preservation, the two added scenarios against `tests/test_addon_options.py`, every pointer, the `Assumption` rows, scope and plain language. It found no lost scenario, no lost condition and no dangling pointer.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **A duplicate SHALL sits under a heading about the other case.** "With no broker host set, the connection settings come from the Supervisor" says "When the form sets `mqtt.host`, all four SHALL come from the form". "A broker host on the form sets all four connection settings" already requires that. A later change to the form's rule could miss the copy, and a reader of the Supervisor requirement alone meets a rule for when a host is set. — **CONFIRMED.**
2. **"The wait ends on time" asserts that the add-on stops, under a requirement that does not say it stops.** Its last THEN, "the add-on stops no later than 65 seconds after the first request", rests on "No Supervisor broker within 60 seconds stops the add-on". — **REFUTED** (see Rebuttals).

### 📌 Suggestions

3. **Plain language.** Four sentences run over 30 words, and "SHALL be left out" hides who leaves the field out. — **CONFIRMED** for the passive voice. Declined for the sentence lengths (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In the delta, under "With no broker host set, the connection settings come from the Supervisor", replace "When the form sets `mqtt.host`, all four SHALL come from the form, as the requirement "A broker host on the form sets all four connection settings" describes." with "When the Configuration form sets `mqtt.host`, the requirement "A broker host on the form sets all four connection settings" decides where all four come from."
2. In design.md, update Decision 4 and the normative word count for the removed duplicate SHALL: 36 SHALL, 5 of them SHALL NOT, and 1 MAY.
3. In the delta, under "A form field that is not set is left out before the core checks the pier", write the rule in the active voice: "The add-on SHALL leave out any Configuration form field that is not set before the core checks the pier, …".

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** Required change 1 is applied in `specs/ha-addon/spec.md`. The SHALL it removes is the same rule that "A broker host on the form sets all four connection settings" states: "the host, port, username and password SHALL all come from the form". So nothing is dropped. Required change 2 is applied in design.md Decision 4 and the SHALL-count risk line. Decision 1's bullet on the form-source sentence now says it is a pointer, so design.md stays consistent with the delta.
2. **Rebutted.** Epic #230 decision 2 says a scenario that tests two behaviors stays whole under the requirement it fits best, and never loses a THEN. "The wait ends on time" is mainly about the 60-second limit on new requests, so it sits with "The wait for the Supervisor's broker lasts at most 60 seconds". Its stop clause is stated by the next requirement, and both land in the same spec. Splitting the scenario would break the epic's check.
3. **Fixed** for the passive voice: required change 3 is applied in `specs/ha-addon/spec.md`, and design.md Decision 4 lists the rewording. **Declined** for the long sentences: each one is long because it quotes a full requirement heading, which a pointer must give word for word.
