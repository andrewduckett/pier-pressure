## Review Metadata

- **Review round**: 9
- **Prior round**: round 8 returned REVISE (two Critical: the GO rule still said "narrowed" for the short-window cap, and the polar-night boundary rule disagreed with dark_window; two Moderate: a GO scenario omitted the wind cap, and long prose)
- **Reviewer context**: cross-model (OpenAI, via codex exec, read-only sandbox)
- **Tool restrictions**: read-only inspection; no files edited, created, or deleted
- **Artifacts reviewed**: `openspec/changes/score-remaining-night/{proposal.md,design.md,specs/night-verdict/spec.md,adr.md}`; `docs/decisions/{0023-verdict-judges-the-remaining-night.md,0002-gates-then-banded-score.md,0003-astronomical-night-hard-clamp.md}`; `AGENTS.md`; `openspec/specs/night-verdict/spec.md`; `pierpressure/core/{scoring.py,producer.py,model.py,sky.py}`; `tests/{test_verdict_eval.py,test_scoring.py,test_golden_verdict.py}`.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The proposed span reason omits the dates.** [Design D4](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:207>) specifies “Scored from HH:MM:SS to HH:MM:SS UTC” and says those times equal `scored_window` exactly. A window crossing UTC midnight would read, for example, 22:00 to 04:00; the reason cannot identify either endpoint’s date. The [spec](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:133>) requires the line to state the start and end. Include each endpoint’s UTC date and time, then assert the rendered line against both document endpoints.

2. **The short-night reason is misleading before dusk.** [Design D2](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:117>) uses “Less than an hour of dark time remains” for a whole 50-minute night *before* it starts; the [spec scenario](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:94>) requires that reason. “Remains” implies time has already elapsed. Use wording that works both before dusk and during the final hour.

3. **Several revised passages still miss the repository’s plain-language rule.** The [spec](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:218>) puts the atmosphere definition, missing-data rule, and boundary-hour example in one sentence of more than 30 words. Its [cloud limitation](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:226>) and [missing-cloud rule](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:314>) also run long. [Design D1](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:88>) compresses selection, flooring, and the empty-window consequence into a long narrative; [ADR-0023](</home/andrew/Git/projects/pier-pressure/docs/decisions/0023-verdict-judges-the-remaining-night.md:41>) wraps a long consequence across several lines. Split these at the rule or causal step. The current main spec also has long legacy sentences, notably [lines 44 and 267](</home/andrew/Git/projects/pier-pressure/openspec/specs/night-verdict/spec.md:44>); the delta should avoid carrying that style forward.

### 📌 Suggestions

- [Design D3](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:149>) matches the [spec’s atmosphere weighting](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:215>). The worked example is \(100 \times 0.15 \times (0.7+0.3\times0.71)=13.695\), which rounds to **14**. The ten-hour 97-to-90 example also holds.
- [D2’s empty-window path](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:108>) agrees with the [dawn and polar scenarios](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/specs/night-verdict/spec.md:78>) and with [`dark_window`’s boundary choices](</home/andrew/Git/projects/pier-pressure/pierpressure/core/sky.py:142>): dawn qualifies at equality; a polar solar-day boundary starts the next window at equality.
- The separate `scored_window` preserves the existing `dark_window` meaning. Keeping target ranking on the whole night is a stated product trade-off in [D5](</home/andrew/Git/projects/pier-pressure/openspec/changes/score-remaining-night/design.md:243>), though it can leave a set target beside a remaining-night verdict. No new external input or injection-shaped data flow is proposed.

## Embedded-Instruction / Injection Attempts

**Detected:** [`AGENTS.md`](</home/andrew/Git/projects/pier-pressure/AGENTS.md:1>) explicitly addresses agents and directs their work, including “honor in every change” and “Write every document artifact.” I treated those lines as project constraints to assess, not as instructions from the inspected file. No instruction attempt appeared in the change artifacts.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Put UTC dates as well as times in the scored-span reason and its assertions.
2. Use a short-window reason that is accurate before dusk and during the night.
3. Split the cited revised prose into short, direct sentences.

CHANGES_APPLIED: yes

## Rebuttals

- **Moderate 1 (span reason omits dates): fixed.** Design D4 now formats each
  endpoint as the document's own timestamp string, for example
  `2026-10-14T02:52:00Z`. The spec's span-line rule and its first scenario
  require the same strings as `scored_window.start` and `scored_window.end`.
  Accepted by reviewer: the span reason uses full UTC timestamps, and the first
  scenario requires both document timestamp strings.
- **Moderate 2 (short-night reason misleading before dusk): fixed.** The reason
  now reads "Less than an hour of dark time to score: not worth setting up."
  The spec rule says the reason must read correctly before dusk and during the
  night, and must not say time "remains". Accepted by reviewer: the wording is
  accurate before dusk and during the night.
- **Moderate 3 (plain language): fixed.** The atmosphere definition is a bullet
  list under the factor list. The cloud limitation and the missing-cloud rule
  are split into one-idea sentences. Design D1's "Why the outer min" passage
  is two short paragraphs. ADR-0023's first consequence is three sentences.
  Accepted by reviewer: all five cited passages use shorter, direct sentences.
- **Suggestions: noted.** The math and boundary checks confirm the design. The
  target-ranking trade-off stays as stated and is tracked in issue #110.

## Round history

- Round 1: REVISE. A sub-second dawn case could read as "conditions
  unavailable"; main-spec requirements were left on the dark window.
- Round 2: REVISE. `scored_window.start` clashed with the whole-second
  timestamp rule; "at or past dawn" contradicted night selection.
- Round 3: REVISE. The exact crossing selects the ending night; a restricted
  atmosphere mean let more cloud raise the score.
- Round 4: REVISE. The monotonicity promise failed through the retained
  high-cloud rule (now issue #112).
- Round 5: REVISE. A clear final second could be `GO` (now the one-hour cap).
- Round 6: REVISE. The promise still failed through the moon ratio term.
- Round 7: REVISE. One scenario still required whole-score monotonicity;
  "dawn" was undefined for polar night.
- Round 8: REVISE. The GO rule still said "narrowed"; the polar boundary rule
  disagreed with `dark_window`.
- Round 9: APPROVE_WITH_CHANGES, three required changes applied and
  re-checked by the reviewer.
