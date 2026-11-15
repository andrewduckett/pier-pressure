## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the working tree was clean before and after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, docs/decisions/0038, relevant source files, at commit `8976c51`
- **Effort**: low (design.md's scrutiny tier)

The resolver exited 5 ("the session stopped to ask"), but the review thread had
completed with its full findings and no pending question. The findings below
come from that thread's final message.

## Findings

### 🔴 Critical (blocking)

1. **The line says "Confidence lowered." when the MEDIUM clamp leaves the value
   unchanged.** A day before dusk with a raw value of 50 and `DISAGREE`
   agreement, confidence is 40 with or without a contradicting report, yet a
   factor below 1 would still add the line. Check: contradictions.
   **CONFIRMED.** Fixed by required change 1.
2. **The term is measured before the no-cloud check, so it could leak into a
   no-cloud verdict.** Before dusk, the instant's hour can carry low and mid
   cloud while the scored window has no cloud data. Design DD5 measured the term
   beside agreement, which happens before the no-cloud path, and did not say that
   path drops it. Check: contradictions (spec "A fixed confidence adds no line").
   **CONFIRMED.** Fixed by required change 2.

### 🟡 Moderate

3. **An obscured sky with no base counts as clear.** `parse_metar` keeps a
   missing base as `None` (`pierpressure/conditions/metar.py`), so `VV///` gave
   an observed cloud of 0 under D5. Check: assumption rows. **CONFIRMED.** Fixed
   by required change 3.
4. **A pier whose cloud comes from NWS or 7Timer! never gets the check.** Only
   the Open-Meteo providers declare `cloud_low` and `cloud_mid`
   (`pierpressure/core/providers.py`), and nothing tells the user. Check: scope.
   **CONFIRMED.** Fixed by required change 4, as documentation; using total cloud
   instead would compare high cloud the station cannot see.

### 📌 Suggestions

5. **"Confidence falls when the forecast is stale, data is missing or forecasts
   disagree" is left unmodified.** Check: contradictions. Declined, see
   Rebuttals.
6. **Some sentences exceed 30 words** (spec, ADR-0038 Context). Check: plain
   language. Partly fixed by required change 5.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Spec "A lowered confidence adds one observed-cloud line": the line appears
   only when the observation makes `confidence.value` lower than without it. The
   clamp scenario gains "no reason line begins with `Observed cloud`". Design
   DD5 computes confidence with and without the term and sets
   `Decision.observed` only when the value falls.
2. Design DD5: the three fixed-confidence paths, the no-cloud path included,
   return `observed=None` whatever the term measured.
3. Spec "The observed cloud is the most cloud…": `OVX` and `VV` count as 100
   whatever their base, with a new scenario for `VV` with no base. Brainstorm D5
   and design DD1 say the same.
4. Design DD7: the README's `metar_station` row says the check needs a cloud
   forecast with low and mid layers, which the Open-Meteo providers give and NWS
   and 7Timer! do not.
5. Split the long sentence in "The observation factor needs a usable
   observation…" and in ADR-0038's Context.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1 (spec requirement text and clamp scenario; design
   DD5).
2. Fixed: required change 2 (design DD5).
3. Fixed: required change 3 (spec requirement and scenario; brainstorm D5;
   design DD1).
4. Fixed: required change 4 (design DD7).
5. Declined: the requirement's "SHALL fall when" lists causes without claiming
   they are the only ones. The modified "Confidence is always present…" names
   every input, and the added requirement states the observation's effect on
   its own. Changing the heading would need a rename for no change in behavior.
6. Partly fixed by required change 5. The 46-word sentence in "A lowered
   confidence adds one observed-cloud line" quotes the line's exact template,
   which a test asserts, so it stays whole.
