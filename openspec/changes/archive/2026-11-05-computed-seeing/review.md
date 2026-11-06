## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (Gemini, `gemini-4-argon`, through the t3 resolver)
- **Independent**: yes. Claude wrote the plan, and Gemini reviewed it.
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean before and after.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0033 and the relevant source files, at commit `b9b9485`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Unchanged main-spec requirements contradict the delta.** CONFIRMED.
   - Check: contradictions.
   - The main conditions spec's *The computed source fills transparency at its place in the order* has two scenarios that expect `seeing` from `seven_timer`, or no seeing. Their `open_meteo` would now send the seeing column, so `computed` fills seeing.
   - *The snapshot records when its data was issued* says that series from one provider carry one issue time. The two computed series can now differ.
2. **A partial seeing column wins the bundle and blocks a later complete model.** CONFIRMED.
   - Check: assumptions, and where it stops working.
   - The fill counts a provider as having returned a bundle when any member has a value. A declaring model that sends part of the column therefore wins the bundle, and seeing fails. The design's risk line said the bundle would fall through to the next model, which is wrong in this case.
3. **The tropopause scan has no guard for heights that don't increase upward.** CONFIRMED.
   - Check: where it stops working.
   - DD4 guarded the bad-layer test against such heights, but not the tropopause test. A flat pair of heights could divide by zero, or falsely cap the count at 500 hPa.
4. **The raw potential-temperature gradient counts normal upper-air cooling as bad.** CONFIRMED.
   - Check: assumptions, and worked numbers.
   - Potential temperature's gradient grows with `(1000 / p) ^ 0.286`. Above about 250 hPa, air cooling at 6.5 K per km exceeds 0.5 K per 100 m. Summer nights with a high tropopause would therefore start with one to three bad layers. ADR-0033 claimed the opposite.

### 📌 Suggestions

5. **The primary seam can't inject a per-variable raising derivation, and the whole-call guard gives an unprefixed error.** CONFIRMED.
   - Check: test seams, and contradictions.
6. **Several sentences exceed 30 words.** Partly CONFIRMED.
   - Check: plain language.
   - The long ones are mostly scenario `WHEN` clauses that list conditions, and the ADR's front-matter description.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. **Finding 1.** In `specs/conditions/spec.md`, add MODIFIED blocks for two main-spec requirements:
   - *The snapshot records when its data was issued*: it now excepts the computed source's series.
   - *The computed source fills transparency at its place in the order*: its two seeing-dependent scenarios now say that Open-Meteo returns no seeing column.
2. **Finding 2.** In `design.md` Risks, correct the fall-through line. Add the partial-column case and its mitigation: the health error, reordering, and a README note.
3. **Finding 3.** Require the next level to be higher before a level can be the tropopause, in the spec's tropopause requirement and in design DD4.
4. **Finding 4.** Measure a bad layer's stability the same way at every height: temperature falls by less than 0.476 K per 100 m, or rises. That is the 0.5 K per 100 m potential-temperature threshold, measured at 1000 hPa.
   - The user chose this on 2026-11-05.
   - Update brainstorm D4, the spec's bad-layer requirement with two new scenarios, design DD4, and ADR-0033's decision, consequence and alternatives.
5. **Finding 5.** In design DD3, `ComputedSource` holds its two derivations as replaceable fields. In DD5, a whole-call failure gives the error kind per declared variable, in the `<variable>: <reason>` form.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: two new MODIFIED requirements at the end of `specs/conditions/spec.md`.
2. Fixed: `design.md`, Risks, now has two lines on a model that drops the column, one for all of it and one for part of it. The fill rule stays as ADR-0027 sets it. Making a bundle win only when it is complete would change every bundle's fill, which is outside this change's scope.
3. Fixed: `specs/conditions/spec.md`, *Bad layers are counted between the pier's ground and the tropopause*, and `design.md` DD4 step 1.
4. Fixed as the user decided:
   - `brainstorm.md` D4
   - `specs/conditions/spec.md`, *A bad layer is a strongly stable layer*, with the new scenarios *A layer high up cooling at the standard rate is not bad* and *A layer cooling slowly is bad*
   - `design.md` DD4
   - ADR-0033's Decision, its Consequences, and its new Alternative 4
5. Fixed: `design.md` DD3 and DD5.
6. Declined. The long sentences are scenario conditions and ADR front matter. Splitting a `WHEN` clause would split one test condition across lines, which makes it harder to read as one case.
