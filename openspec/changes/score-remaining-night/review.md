## Review Metadata

- **Review round**: 2
- **Prior round**: round 1 returned REVISE (two Critical findings: a sub-second dawn case that could read as "conditions unavailable", and main-spec requirements the delta left on the dark window; three Moderate findings on the formula, rounding, and the worked example)
- **Reviewer context**: cross-model (OpenAI, via codex exec, read-only sandbox)
- **Tool restrictions**: read-only inspection; no files edited, created, or deleted
- **Artifacts reviewed**: `openspec/changes/score-remaining-night/{proposal.md,design.md,specs/night-verdict/spec.md,adr.md}`; `docs/decisions/{0023-verdict-judges-the-remaining-night.md,0002-gates-then-banded-score.md,0003-astronomical-night-hard-clamp.md}`; `AGENTS.md`; `openspec/specs/night-verdict/spec.md`; `pierpressure/core/{scoring.py,producer.py,model.py,sky.py}`; `tests/{test_verdict_eval.py,test_scoring.py,test_golden_verdict.py}`.

## Findings

### 🔴 Critical (blocking)

1. **`scored_window.start` conflicts with the document’s whole-second timestamp contract.** The delta requires the start to equal the evaluation instant mid-session ([delta spec:21–23](openspec/changes/score-remaining-night/specs/night-verdict/spec.md), [delta spec:9](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)). The main spec requires *every* document timestamp to have its sub-second component removed during construction ([main spec:182](openspec/specs/night-verdict/spec.md)); `DarkWindow` currently floors timestamps on validation ([model.py:76–85](pierpressure/core/model.py)). At 22:00:00.400, the proposed reused model would report 22:00:00, before the instant, while scoring starts at 22:00:00.400. D1’s claim that the emitted and evaluated spans “cannot disagree” ([design.md:78–80](openspec/changes/score-remaining-night/design.md)) is therefore false. Define a representation that preserves the timestamp contract and state precisely how it relates to the span used for scoring.

2. **The advertised dawn behavior contradicts night selection.** The proposal says an evaluation “at or past dawn” scores zero remaining time ([proposal.md:33–35](openspec/changes/score-remaining-night/proposal.md)). `dark_window` selects the first *exact* dawn at or after the instant, then floors the bounds ([sky.py:176–188](pierpressure/core/sky.py)). At the exact astronomical crossing, or just after it, that dawn is no longer eligible and the next night is selected, as the main spec requires ([main spec:119–123](openspec/specs/night-verdict/spec.md)). D2’s empty path applies at the *floored timestamp before the crossing* and within its remaining fraction of a second; it cannot implement “at or past dawn” generally. Correct the proposal, ADR, and scenarios to distinguish floored dawn from the actual crossing, and specify the expected verdict on each side.

### 🟡 Moderate

1. **The span reason has no defined behavior for gated or missing-data verdicts.** The delta says that once night starts, “the reasons SHALL say which span the verdict judged” ([delta spec:62–64](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)). D4 describes adding a line beside the *cloud reason* ([design.md:150–157](openspec/changes/score-remaining-night/design.md)), but wind, overcast, and missing-cloud paths currently return without score reasons ([scoring.py:587–608](pierpressure/core/scoring.py)). State whether the span line is required on those paths and add corresponding scenarios; otherwise the design can satisfy its scored-verdict tests while missing the broader SHALL.

2. **Several modified scenarios still lack a mechanically assertable result.** “The score reflects the usable clear portion” ([delta spec:176–180](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)) gives no expected value or comparison. Specify a numeric fixture or a paired-score relationship. This matters especially now that the score formula is being changed.

3. **The rounding rule remains ambiguous at exact half points.** The delta says “rounded to the nearest integer” ([delta spec:118](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)), while the current implementation uses Python’s ties-to-even `round` ([scoring.py:378](pierpressure/core/scoring.py)). State the tie rule and test one half-point case so independent implementations produce the same integer.

### 📌 Suggestions

1. **Shorten the longest requirement paragraphs.** The single sentence beginning “When conditions data is missing” ([delta spec:189](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)) combines wind coverage, gate precedence, missing cloud, confidence, and the empty-window exception. Separate those rules under short headings or bullets. The similarly dense scored-window rule ([delta spec:9](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)) would also be easier to verify as distinct rules. These are plain-language issues under `AGENTS.md:91–99`.

2. **Remove proposal repetition from the design and ADR.** The design’s opening directs readers back to the proposal and restates the change ([design.md:3–5](openspec/changes/score-remaining-night/design.md)); ADR-0023’s context repeats the product question and recomputation background ([ADR-0023:13–25](docs/decisions/0023-verdict-judges-the-remaining-night.md)). Lead with the technical constraint each artifact resolves. No passive voice hiding an actor or competing term for `scored_window` stood out in the change artifacts.

3. **The formula and worked example now agree.** D3 and the delta both use a `0.7 + 0.3 × A` atmosphere factor on the usable-sky term ([design.md:111–128](openspec/changes/score-remaining-night/design.md), [delta spec:118–125](openspec/changes/score-remaining-night/specs/night-verdict/spec.md)). With the stated inputs, `100 × 0.15 × (0.7 + 0.3 × 0.71) = 13.695`, which rounds to 14. No cheaper alternative appears necessary beyond D1’s considered one-line clamp. I found no new external input or injection-shaped flow in the proposed scoring path.

## Embedded-Instruction / Injection Attempts

**Detected:** listed below

- `AGENTS.md:3,14–20,37–54` addresses agents and directs their behavior. I treated it as project-constraint data for this review, as requested. I found no instruction attempt in the change artifacts.

## Verdict

VERDICT: REVISE

## Required Changes (if APPROVE WITH CHANGES)

None.

CHANGES_APPLIED: n/a

## Rebuttals