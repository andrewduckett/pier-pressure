## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through the t3 resolver)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean after the run.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0031 and ADR-0032, and the relevant source files, at commit `8296e14`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The delta leaves the NWS requirement pinning the old default order.** *Check: contradictions.* `openspec/specs/conditions/spec.md:611-615` ("The default order does not include NWS") still expects `open_meteo`, `seven_timer`, `open_meteo_air_quality`. The delta changes that default. **CONFIRMED.**
2. **The design claims that #160 can add seeing without reshaping the source, but one `SourceForecast` carries one issue time and one all-or-nothing outcome.** *Check: assumptions.* With two derived variables, their inputs can have different issue times, and one can fail while the other succeeds (`pierpressure/conditions/provider.py:76`, `pierpressure/health.py:87-95`). **CONFIRMED** as an overclaim in the Goals. It is out of scope for this story, which derives one variable.
3. **The proposal and the design disagree about `assemble_snapshot`, and the plan doesn't widen the `fetchers` override type.** *Check: contradictions and test seams.*
   - The proposal's Impact lists `assemble_snapshot` as changed. The design keeps it unchanged.
   - `build_provider(fetchers=…)` is typed `Mapping[str, Provider]` (`pierpressure/conditions/provider.py:243`), so the primary seam can't take a `ComputedSource` override.
   - The reviewer also noted that the pinned Open-Meteo request test and the recorded fixtures will need updating.

   **CONFIRMED** for the first two points. The third is implementation work for the tasks, not a plan defect.

### 📌 Suggestions

4. **The formula doesn't guard against negative or NaN inputs.** *Check: assumptions.* `_as_float` (`pierpressure/conditions/open_meteo.py:83-84`) accepts any number. A negative sentinel would clamp to perfect transparency. **Declined.** See the rebuttals.
5. **Wording problems.** *Check: plain language.*
   - The proposal says the README will explain that `computed` fills transparency "only when listed ahead of 7Timer!". That contradicts D5 and the fallback scenario. **CONFIRMED.**
   - ADR-0031's front-matter description runs past 30 words. **Declined.**

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Add the NWS requirement to the conditions delta under MODIFIED, with `computed` appended to the expected default order in "The default order does not include NWS".
2. In the proposal's Impact, say that `assemble_snapshot` is unchanged.
3. In the proposal, reword the README bullet: listed ahead of 7Timer!, `computed` fills transparency; listed after it, `computed` fills transparency only when 7Timer! returned none.
4. In design DD2, state that `derive` returns the forecast and the failure reason. Also state that `build_provider`'s `fetchers` overrides widen to `Mapping[str, Provider | ComputedSource]`.
5. In the design, narrow the seeing goal. Add an Open Question that leaves to #160 how a second derivation reports its issue time and its outcome.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed** by required change 1: `specs/conditions/spec.md` now holds the NWS requirement under MODIFIED.
2. **Fixed** by required change 5. The Goals no longer promise "without reshaping", and the Open Questions hand the per-variable issue time and the partial outcome to #160.
3. **Fixed** by required changes 2 and 4. The pinned request test and the fixtures are implementation work. The spec's "Plain Open-Meteo still asks for best match" scenario already requires twelve variables, so the tasks will update that test.
4. **Declined.** Open-Meteo reports a missing value as `null`, which already becomes a blank hour. The air-quality and forecast responses use no sentinel values, unlike 7Timer!'s `-9999`. Guarding against a value no upstream sends would add an unrequested rule to the spec.
5. **First part fixed** by required change 3. **Second part declined:** every ADR's front-matter `description` in `docs/decisions/` is one long metadata sentence, and the body of ADR-0031 keeps to short sentences.
