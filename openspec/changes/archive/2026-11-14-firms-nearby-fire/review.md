## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the working tree was clean before and after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, docs/decisions/0039, relevant source files, at commit `038f314`
- **Effort**: high (design.md's scrutiny tier)

The reviewer's own last line said REVISE. The verdict below follows from the
adjudicated findings: both Critical findings are closed by small listed edits,
so no Critical finding stays open.

## Findings

### 🔴 Critical (blocking)

1. **A day range of 1 drops yesterday's detections after 00:00 UTC.** With no
   date, the FIRMS area API returns TODAY − (DAY_RANGE − 1) to TODAY in UTC.
   At 8 pm in the Americas the UTC date has rolled over, so the afternoon
   NOAA-20 pass, 4 to 8 hours old, is not returned. The core's 24-hour rule then
   has nothing to count. Check: assumptions (brainstorm D5).
   **CONFIRMED** against FIRMS's area API page. Fixed by required change 1.
2. **The log filter lives only in `main()`, so tests and records formatted later
   could leak the key.** pytest's `caplog` handler is added after `main()` would
   run. Clearing `args` without formatting first would break the message.
   Check: secret handling, test seams.
   **PARTLY CONFIRMED.** Production sets up logging once, in
   `pierpressure/__main__.py:191`, and adds no handler later, so the production
   path is covered. The design did not say how tests reach the filter, or how it
   formats a record before it masks one. Fixed by required change 2.

### 🟡 Moderate

3. **Health scenarios write times with `Z`, but delivery publishes `+00:00`.**
   Check: scenario testability.
   **REFUTED.** The main spec writes instants this way already: the METAR health
   scenario at `openspec/specs/ha-delivery/spec.md:1352` says
   `2026-11-14T21:30:05Z`. A scenario names an instant, and the delivery tests
   compare it in the delivery's own format.
4. **DD6 validates the block in `load_app_config`, which `load_config` never
   calls.** An invalid `firms` block loaded through `load_config` would then
   reach `AppConfig.model_validate` and quote its input. Check: contradictions,
   secret handling.
   **CONFIRMED.** `explainer` is validated in `build_config`
   (`pierpressure/core/config.py:503`, `:560`). Fixed by required change 3.
5. **DD2's sort key negates a `datetime`, and "equally near" is undefined.**
   Two detections 12.1 km and 12.4 km away both read "12 km", but a float
   distance never ties. Check: scenario testability, contradictions.
   **CONFIRMED.** Fixed by required change 4.

### 📌 Suggestions

6. **Two requirement sentences run over 30 words.** The counting rule in
   `specs/night-verdict/spec.md`, and the failure rule in
   `specs/conditions/spec.md`. Check: plain language.
   **CONFIRMED.** Fixed by required change 5.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Ask FIRMS for a day range of 2, today and yesterday in UTC, and let the core's
   24-hour rule cut the window: `specs/conditions/spec.md` (the URL, its
   scenario and a sentence on why), brainstorm D5 and the proposal's fetch line.
2. In design DD5, name the seam `mask_key(key)` in `pierpressure/redact.py`. It
   adds the filter to every root handler present when it is called. `main()`
   calls it after `basicConfig`. Spell out that the filter masks
   `getMessage()`, clears `args`, and masks `exc_text` and `stack_info`. Say
   that a log test calls `mask_key` after `caplog` is in place.
3. In design DD6, validate the `firms` block in `build_config`, beside
   `explainer`, not in `load_app_config`.
4. In design DD2, choose the nearest by `(rounded_km, -detected_at.timestamp(),
   index)`. In `specs/night-verdict/spec.md`, define the nearest as the
   smallest whole-kilometre distance, rounded as the line rounds it, with the
   tie scenario at 12.1 km and 12.4 km.
5. Break the two long requirement sentences into lists.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: `specs/conditions/spec.md` asks for `.../<box>/2` and says why;
   brainstorm D5 and `proposal.md` match.
2. Fixed: design DD5 now names `mask_key`, the record handling and the test
   seam. The production path was already covered, as the finding notes.
3. Rebutted: `openspec/specs/ha-delivery/spec.md:1352` writes the same instant
   with `Z`. The notation is the spec's, not the wire format.
4. Fixed: design DD6 names `build_config`.
5. Fixed: design DD2 gives the numeric sort key and the rounding first; the
   night-verdict requirement "The nearest of equally near detections is the
   latest" defines the nearest by whole kilometres.
6. Fixed: both requirements are now lists.
