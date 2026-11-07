## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3; the meta line says `"independent": true`)
- **Independent**: yes
- **Tool restrictions**: read-only: the reviewer ran in plan mode and could not write files; `gitClean: true` after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `ecd8319`
- **Effort**: medium, from design.md's scrutiny tier

## Findings

Each finding was checked against the repository. All eight are CONFIRMED.

### 🔴 Critical (blocking)

1. **The "min sensor is unavailable" scenario contradicts its own rule, and D10 disagrees with DD5** (check: contradictions). The scenario left the max sensor out of Home Assistant, so rule 1 gives `Not found`, not `Unavailable`. D10 read as sensor-first order; DD5 and the spec use cause-first order. CONFIRMED: `specs/night-card/spec.md`, the scenario's WHEN named only the min sensor.
2. **Two main-spec requirements become false and were not modified** (check: contradictions). "The card draws the four cloud rows" puts Cloud low straight after Cloud cover (`openspec/specs/night-card/spec.md:187-194`). "Hovering over a row's message names its sensor" (`:819-837`) covers every row, but `Needs two forecasts` names no sensor. CONFIRMED.

### 🟡 Moderate

3. **The docs requirement names a per-pier `providers` setting, and misses a failed provider and the first-verdict note** (check: assumptions). `providers` lives under the top-level `conditions` (`pierpressure/core/config.py:89-100`). A listed second cloud provider that fails also gives `Needs two forecasts`. `docs/night-card.md` says every row says "No forecast" before the first verdict, which becomes false. CONFIRMED.
4. **Swapping a min above the max draws a disagreement no forecast gave** (check: assumptions). Home Assistant applies the two sensors' updates one at a time, so for a moment an hour can pair a new min with an old max. The card already rejects an inverted dark window or target window (`card/src/strip.ts:28`, `:335`). CONFIRMED.
5. **The 32 px row leaves its label and message at the top, a bar can pass the cell's rounded corners, and the by-eye check never shows a bar** (check: test seams). `.label` and `.missing` have a 16 px line height; `.cell` has no `overflow: hidden`; `scripts/dashboard_check.py` uses the default providers, which give one cloud forecast. The spec also left out the row's shades and height. CONFIRMED.
6. **`make_timeline` leaves the two keys null, and one scenario asserts Home Assistant's entity ids** (check: test seams). `tests/conftest.py:532-560` fills every field but these two, so the per-key state tests and the 120-hour recorder test would not test numbers. The entity-id line asserts Home Assistant's slugging, which the fake MQTT client cannot see. CONFIRMED.
7. **DD6 misses two sections of `docs/night-timeline.md`, and clamping had no scenario** (check: scenario testability). "What the timeline is" and "Why the Verdict sensor leaves the timeline out" both list the keys or sensors; `tests/test_timeline_docs.py:218-223` checks the second. The clamp rule had no scenario, and DD3 did not say whether `Band.low` and `Band.high` are clamped. CONFIRMED.

### 📌 Suggestions

8. **Long sentences, a wrong row range, and "variable" for a value that is not one** (check: plain language, vocabulary). The docs requirement had a 53-word sentence; D10 and D18 were over 30 words. "One per timeline sensor from Sun altitude to Precipitation probability" does not match the sensor order. `cloud_cover_min` is not a glossary Variable (`tests/test_conditions_model.py:184`). CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. brainstorm.md: D6's source becomes Evidence (#186 Scope, the 16 px track). D10 says cause-first order, min first, in short sentences. D18 sets both sensors' states through Home Assistant's state API so the check sees real bars.
2. design.md: Test Seams names the `make_timeline` defaults and the card tests that count rows. DD3 skips an hour whose min is above its max, and says `Band.low`, `Band.high`, `data-low` and `data-high` are clamped while the hover text is not. DD4 adds `overflow: hidden` on the column and a 32 px line height for the row's label and message. DD6 adds the two `docs/night-timeline.md` sections, the first-verdict note, and both causes of `Needs two forecasts`, with `providers` under `conditions`.
3. specs/ha-delivery/spec.md: the names-and-units scenario asserts the unique ids and the name-to-key rule, not Home Assistant's entity ids.
4. specs/night-card/spec.md: split the column and range-bar requirements into short sentences in the active voice; add the row's shades and height, a clamp scenario, a 100% scenario and a min-above-max scenario; complete the "min sensor is unavailable" scenario and add one where a missing sensor comes before an unavailable one; name both causes and `conditions` in the docs requirement; fix the sixteen-rows wording; and modify "The card draws the four cloud rows" and "Hovering over a row's message names its sensor", and the docs bullet on hovering over a message.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: the scenario now has the max sensor available, a new scenario proves `Not found` comes before `Unavailable`, and D10 states cause-first order (required changes 1 and 4).
2. Fixed: both requirements are now MODIFIED in `specs/night-card/spec.md`, and the docs bullet says what each message's hover shows (required change 4).
3. Fixed: the docs requirement names `providers` under `conditions`, both causes and the health sensor; DD6 covers the first-verdict note and the add-on's config file (required changes 2 and 4).
4. Fixed: DD3 and the spec skip an hour whose min is above its max (required changes 2 and 4).
5. Fixed: DD4 sets `overflow: hidden` and the 32 px line height; the spec states the shades and height; D18 sets the sensors' states so a real browser draws bars (required changes 1, 2 and 4).
6. Fixed: Test Seams names the fixture change, and the ha-delivery scenario asserts unique ids and the name-to-key rule (required changes 2 and 3).
7. Fixed: DD6 lists both sections; the spec has clamp and 100% scenarios; DD3 states which values are clamped (required changes 2 and 4).
8. Fixed for the spec and ledger sentences and the row wording. The docs will say "timeline value" for the two sensors, as `docs/night-timeline.md` does; no glossary change is needed.
