## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini, `gemini-3.8-flash`, through `lets delegate review run`; a first attempt on `gemini-4-argon` returned only a quota error and was discarded)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `d1fe16d`
- **Effort**: medium, from design.md's scrutiny tier

## Findings

### 🔴 Critical (blocking)

1. **`tests/test_model.py` is missing from the plan's seams and blast radius.** `TIMELINE_ENTRY_KEY_ORDER` (line 36) pins the ten-key entry, and `test_timeline_entry_rejects_unknown_keys` (line 308) probes the extra-key guard with `dew_point`, which becomes a real field. Design.md named `tests/test_producer_timeline.py` as the key-order pin, where no such assertion exists. Check: test seams. **CONFIRMED.**

### 🟡 Moderate

2. **The night-verdict delta ADDs a weather-values requirement instead of MODIFYing "Entry values carry each source's reading for the hour".** The reviewer reads the two as overlapping and contradictory at archive. Check: contradictions. **REFUTED**, see Rebuttals.
3. **`test_a_timeline_discovery_carries_its_unit` in `tests/test_timeline_sensors.py` (line 150) hardcodes six key-unit pairs,** so the six new units would go unasserted. Check: test seams. **CONFIRMED.**
4. **`test_page_tables_each_sensors_unit` in `tests/test_timeline_docs.py` (line 186) checks `%`, `km/h` and `°` only,** so `°C` in the docs table would go unguarded. Check: test seams. **CONFIRMED.**
5. **The parser plan proves the null path but not the absent-array path.** No test in `tests/test_conditions_provider.py` feeds a payload with an array missing from `hourly`, though the design's risk list relies on that guard. Check: assumptions. **CONFIRMED.**

### 📌 Suggestions

6. **Some sentences exceed 30 words:** the ha-delivery delta's requirement text (a fourteen-key list), its 48-entry scenario, and the proposal's Why. Check: plain language. **Declined**, see Rebuttals.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md: add `tests/test_model.py` to Context, Test Seams and Blast radius; in DD6, extend `TIMELINE_ENTRY_KEY_ORDER` with the six keys and move the extra-key probe to a key outside the schema; point the key-order risk at `tests/test_model.py`.
2. design.md DD6: extend `test_a_timeline_discovery_carries_its_unit` with the six key-unit pairs.
3. design.md DD6: add `°C` to the docs unit check in `tests/test_timeline_docs.py`.
4. design.md DD4: add a parser test with one weather array absent from `hourly`, asserting that field is `None` for every hour and the others keep their values.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** design.md Context, Test Seams, Blast radius, DD6 and Risks now name `tests/test_model.py`, the key-order pin and the moved probe (commit "docs: apply plan review changes").
2. **Rebutted.** The existing scenario says the five base fields are null for an hour the base source lacks; the added requirement says the six weather keys are null too. Both stay true after archive, so there is no contradiction. The spec-writing skill prefers ADDED for a new concern that leaves an existing requirement's behavior alone, and the existing requirement's text, units and scenarios do not change.
3. **Fixed.** DD6 names the unit pin and the six pairs.
4. **Fixed.** DD6 names the `°C` check.
5. **Fixed.** DD4 adds the absent-array parser test.
6. **Declined.** The long sentences are key lists; splitting a list of fourteen keys into sentences adds words without adding clarity. The proposal's Why is two sentences of ordinary length for a cause-and-effect statement.
