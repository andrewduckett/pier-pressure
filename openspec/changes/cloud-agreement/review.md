## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini, `gemini-3.8-flash`, through the `t3` resolver; a first attempt on `gemini-4-argon` returned only a quota error and no review)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0029, relevant source files, at commit `ba6e286`
- **Author**: this session (claude family)

## Findings

### 🔴 Critical (blocking)

1. **Agreement factor pushes a complete forecast into LOW.** With `_CONFIDENCE_FLOOR = 0.50` and `_BAND_MEDIUM = 40` in `pierpressure/core/scoring.py`, a fresh, complete forecast a day before dusk sits at 50; `× 0.67` gives 34, which is LOW. The plan's guarantee only covered a start of 100. Check: contradictions. **CONFIRMED.**
2. **Presence condition contradicts DD3.** The spec said the entry is present when two providers each cover any scored hour; DD3 returns `None` when no hour has two readings. Disjoint coverage left the document undefined. Check: contradictions. **CONFIRMED.**
3. **DD5 claimed the early-exit paths cannot hold two cloud providers.** A polar-summer pier with no dark window, or an instant at the end of the night, still has alternates. The spec already said `{}` there; the design's reasoning was wrong and left `Decision` unspecified on those paths. Check: contradictions. **CONFIRMED.**

### 🟡 Moderate

4. **Zero weights report `spread 0` for 90 versus 100.** Check: contradictions. **REFUTED** as to the band, see Rebuttals.
5. **Band on the unrounded mean, spread rounded.** A line could read `spread 15 points` as `agree` one night and `mixed` the next. Check: contradictions. **CONFIRMED.**
6. **`providers` listed alternates that cover no scored hour.** A GFS alternate for days three to seven would be counted as a third voice. Check: contradictions. **CONFIRMED.**

### 📌 Suggestions

7. **Assumption D7 puts the agreement line under a wind-gate NO-GO.** Check: assumption rows. Declined, see Rebuttals.
8. **Sentences over 30 words** in two spec requirements and two design decisions. Check: plain language. **CONFIRMED** for the specs.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Spec and DD4: clamp the agreement factor so a value at or above the MEDIUM threshold before the factor stays at or above it; add the long-lead-time and already-LOW scenarios.
2. Spec and DD3: the `cloud_cover` entry is present exactly when at least one scored hour has values from two or more providers; add the disjoint-coverage scenario.
3. DD4 and DD5: `Decision` carries `agreement` with a default of `None` set on every later path; the two early returns happen before the measure runs.
4. Spec and DD3: decide the band on the rounded spread; add the 14.6 scenario; update the rounding risk row.
5. Spec and DD3: `providers` lists only providers that give a value for a counted hour; add the scenario.
6. Spec: split the two long requirement sentences.

CHANGES_APPLIED: yes

## Rebuttals

- **1, fixed.** Commit `88241b3`: night-verdict delta, requirement "Confidence falls with low agreement", plus two scenarios; design DD4.
- **2, fixed.** Commit `88241b3`: requirement "The document carries cloud agreement", scenario "Providers that never share an hour yield no agreement"; design DD3.
- **3, fixed.** Commit `88241b3`: design DD4 and DD5. The spec scenario "No dark window means no agreement" already pinned the behaviour.
- **4, rebutted.** Zero weights arise only when every hour's lowest reading is at or above `CLOUD_OVERCAST = 90` (`pierpressure/core/scoring.py`, `clarity_weight`). Then every gap is at most 10 points, so the band is `AGREE` whichever weighting applies; only the displayed spread differs, and the user chose spread 0 for that case (brainstorm D2). The 89.9 step the reviewer describes moves the spread from 0 to at most 10 and never moves the band.
- **5, fixed.** Commit `88241b3`: requirement "Cloud agreement is the clarity-weighted mean gap over the scored window", scenario "The band follows the rounded spread"; design DD3 and the risk row.
- **6, fixed.** Commit `88241b3`: `providers` definition and scenario "A provider that shares no counted hour is not listed"; design DD3.
- **7, declined.** A wind-gate NO-GO still carries a confidence, and disagreement lowers it; the line is the only place that says why. The user confirmed D7 in the brainstorm with the gated case named.
- **8, fixed for the specs** in commit `88241b3`. The two design sentences are 31 and 35 words and read clearly; left as they are.
