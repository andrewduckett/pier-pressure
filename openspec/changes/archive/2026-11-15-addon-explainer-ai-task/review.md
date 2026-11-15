## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash,
  through the `t3` resolver)
- **Independent**: yes. The author is the claude family. The review ran in its
  own T3 thread, "Review HA AI Task Explainer". `lets delegate review run` was
  stopped by the author's 10-minute shell limit before it could write its meta
  line, so it has no exit code. The reviewer thread finished on its own with a
  complete review, which is recorded here.
- **Tool restrictions**: read-only by instruction; the reviewer ran in plan
  mode. `git status --porcelain` showed no change from the reviewer.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md,
  `docs/decisions/0042-addon-narrative-may-come-from-home-assistant-ai-task.md`,
  relevant source files
- **Commit reviewed**: a79f68b

## Findings

### 🔴 Critical (blocking)

1. **The form's `enabled` switch can lock a user into a startup conflict.**
   Check: contradictions, trust boundary. The reviewer says the Home Assistant
   UI saves an untouched switch as `false`, and `is_set(False)` is true, so
   `explainer.enabled: true` in `config.yaml` then stops the add-on. A switch
   cannot be returned to unset from the form. Author check: **CONFIRMED in
   part.** The frontend saves only the values the form changed
   (home-assistant/frontend `dev` 502dcdc1,
   `src/panels/config/apps/app-view/config/supervisor-app-config.ts` L384,
   L436-438, L499-501), so an unrelated save does not write `false`. But a
   switch turned on and then off does save `false`, and only YAML mode can
   remove it. The design's mitigation (design.md, old DD6 risk) was weak.

### 🟡 Moderate

2. **The proposal and the design name different files for the new provider.**
   Check: contradictions. proposal.md Impact named `provider.py`; design.md DD1
   names `pierpressure/explain/ai_task.py`. **CONFIRMED.**
3. **Several requirement sentences run over 30 words.** Check: plain language.
   verdict-narrative: "The AI Task instructions are the explainer's existing
   prompt", "A Home Assistant that does not answer…", "An AI Task entity outside
   an add-on…"; ha-addon: "The form's explainer block has three optional
   fields", "The form's switch and AI Task entity…", "The explainer section
   names both ways…". **CONFIRMED.**

### 📌 Suggestions

4. **The error-status scenario leaves out 403.** Check: scenario testability.
   The Supervisor answers 403 when access is denied. **CONFIRMED**; cheap to
   add.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

The reviewer's own line was REVISE, because of finding 1. Finding 1 is fixed by
a small, unambiguous edit listed below, and so are the others. No finding stays
open, so the verdict follows the skill's rule.

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. A form `explainer.enabled` of false counts as not set. brainstorm.md D7 says
   so. design.md DD6 makes `translate_form` drop it, and its risk line is
   replaced. The ha-addon delta's "Each explainer setting on the form joins
   config.yaml on its own" says so, with a new scenario, "A switch set to off on
   the form does not conflict". proposal.md names the `addon_options.py` change.
2. proposal.md Impact names `pierpressure/explain/ai_task.py`.
3. Split each sentence finding 3 names into sentences of 30 words or fewer, with
   no change of meaning.
4. Add 403 to the scenario "An error status gives no narrative", and name the
   Supervisor as a possible answerer.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed by required change 1. The reviewer's broader scenario, that any
   unrelated save writes `false`, is refuted by the frontend source cited
   above; the fix covers the real case either way.
2. Fixed by required change 2.
3. Fixed by required change 3.
4. Fixed by required change 4.
