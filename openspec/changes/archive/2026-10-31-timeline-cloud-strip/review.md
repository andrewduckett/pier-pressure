## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, same family
- **Independent**: no. The ranked list was Gemini first, then every GPT model, then Claude; the resolver refused every Gemini and GPT model and the review ran in a fresh `claude-opus-5-5` session. The meta line records `"independent": false`.
- **Tool restrictions**: read-only: view, grep, glob only. `git status --porcelain` was clean after the run.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0025, relevant source files, at commit `0cdb365`.
- **Effort**: medium, from design.md's scrutiny tier.
- **Reviewer's write-up**: `.workspace/timeline-cloud-strip-review-raw.md` (summary) and the reviewer's full report with file and line references, copied into the summary's findings below.

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **An empty timeline crashes `produce_verdict`** (check: contradictions, failure mode). Design D2 built one Skyfield `Time` with `ts.from_datetimes(hours)`; with no hours Skyfield raises `ValueError`. Empty is the normal case for the astronomy-only fallback, both providers down, and the `empty` golden. CONFIRMED: reproduced, `ValueError: not enough values to unpack (expected 6, got 0)`.
2. **The spec wanted state `15`, the design emitted `"15.0"`** (check: contradictions). `open_meteo._as_float` stores floats, so `str(15.0)` is `"15.0"`, and nothing said how to format. CONFIRMED.
3. **Two scenarios compared against "before the timeline existed"** (check: scenario testability). After the goldens regenerate nothing keeps the pre-change document, and no golden case lacks a dark window. CONFIRMED.
4. **The altitude scenario failed at the rounding edge, and the named test proved nothing about vectorisation** (check: scenario testability, determinism). A true -18.0003 rounds to `-18.0`, not strictly below -18; a sign check cannot detect a last-bit difference between the vector path and `_altitude_deg`. CONFIRMED.
5. **The plan did not name the regression pin it breaks** (check: test seams). `tests/test_rank_targets.py::test_existing_entities_publish_the_same_topics_and_payloads` lists every non-rank publish exactly, including `document.to_json()` as the attributes payload. CONFIRMED.
6. **Brainstorm D6 assumed hourly recomputes** (check: assumption rows). `recompute.interval_seconds` is only `gt=0`, so a 3-hour interval shows an old hour as current, and the attributes did not say which hour the state belongs to. CONFIRMED.

### 📌 Suggestions

7. An unspecified `current` attribute key would have become frozen delivery surface. CONFIRMED.
8. Home Assistant ignores an empty state on a sensor with a unit, so availability alone guards against an earlier value. CONFIRMED.
9. Cloud and wind precision was unspecified, and ADR-0025 said everything was rounded. CONFIRMED.
10. The 72-entry size test understated the real maximum, roughly 120 hours. CONFIRMED.
11. ADR-0025's Alternative 3 argued against a different option from the one brainstorm D3 rejected. CONFIRMED.
12. `make_conditions` cannot express the union cases; the producer docstring and the README topic label go stale. CONFIRMED.
13. Plain language: two sentences over 30 words; "conditions sources" versus the glossary's "conditions providers"; "mid-session" for "inside the dark window". CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Design D2: `altitudes_at(pier, [])` returns `[]` without calling Skyfield; D3 and the risks name the `Conditions(None, None)` producer test; the night-verdict delta's empty scenario asserts the verdict is produced without error.
2. Design D5 and the ha-delivery delta agree: the state and each forecast `value` are the number as the document emits it (`15.0`); scenarios use that form.
3. Night-verdict delta: the no-dark-window scenario compares the document minus `timeline` with the document from the empty conditions value; the "existing fields" scenario becomes "hours outside the dark window change no other field". The golden-diff check stays in design D6 only.
4. Night-verdict delta: "at or below minus 18.0 after rounding"; a new scenario compares the timeline altitudes with the single-instant astronomy at 3 dp; design D2 and the risks name that test.
5. Design D4 names the `test_rank_targets.py` pin and how it is kept, and `make_document` gains a `timeline` parameter.
6. Ha-delivery delta: the attributes carry `available`, `hour` and `forecast`, with `hour` the time the state comes from; the state requirement says it can lag by one recompute interval; brainstorm D6 cites the config interval; design D5 and D7 and the docs page say so.
7. Suggestions 7 to 13 applied as well: `current` dropped for `hour` (6); design D5 states availability alone carries the guarantee (8); the entry-values requirement says cloud and wind pass through unchanged, with a scenario, and ADR-0025's consequence matches (9); the size risk and scenarios use 120 entries (10); ADR-0025 Alternative 3 rewritten to the option D3 rejected (11); design test seams note the fixture gap, the docstring and the README label (12); sentences split, "providers" used for the plural, "inside the dark window" (13).

CHANGES_APPLIED: yes

## Rebuttals

- 1: fixed. design.md D2 short-circuits on no hours; risks list the empty-timeline crash with its test; night-verdict delta "No provider rows yield an empty timeline" asserts production without error.
- 2: fixed. design.md D5 serializes the value as JSON; ha-delivery delta scenarios read `15.0` and `37.0`.
- 3: fixed. night-verdict delta scenarios "The timeline fills without a dark window" and "Hours outside the dark window change no other field".
- 4: fixed. night-verdict delta scenarios "Altitudes agree with the dark window" (at or below -18.0 after rounding) and "Altitudes agree with the single-instant astronomy"; design.md D2 and risks.
- 5: fixed. design.md D4 names the test and the kept guard; `make_document` gains `timeline`.
- 6: fixed. ha-delivery delta attributes requirement and state requirement; brainstorm.md D6; design.md D5 and D7.
- 7 to 13: fixed as listed under required change 7. No suggestion declined.

All findings came from a same-family reviewer. Each was checked against the repository before acceptance; none was taken on trust.
