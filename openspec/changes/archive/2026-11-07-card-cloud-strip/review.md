## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `cc2d416`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Unpinned locale breaks `HH:MM` and every time label in a browser with non-Latin digits.** Check: contradictions (DD5 against the spec's `HH:MM`). In `ar-EG`, `fa-IR` or `bn-BD`, `formatToParts` returns non-Latin digits, so the hour filter in DD6 matches nothing. **CONFIRMED.**
2. **An inverted or multi-year `dark_window` gives a zero or negative axis, or a huge time-label loop.** Check: assumptions (DD7). The core never sends one (`pierpressure/core/sky.py` `dark_window` guarantees `start < end`), but a hand-edited state could, and the card must not divide by zero or freeze. **CONFIRMED.**
3. **Assumption D11 (a label every 3 hours) crowds on a narrow card, doubles a label when clocks go back, and leaves the axis-end rule ambiguous.** Check: assumption rows. A polar-night axis spans 33 hours (`sky.py` `_local_solar_day`), and the card asks for no width (`card/src/pierpressure-card.ts` has no `getGridOptions`). **CONFIRMED.**
4. **The design reads `forecast` without checking for `unavailable`, so a sensor that kept its attributes would draw stale cells.** Check: contradictions (DD7 against "A missing cloud sensor leaves an empty row"). **CONFIRMED.**
5. **The test seams omit `tests/test_night_card_doc.py`, and the docs scenario asserts only two of the six topics its requirement names.** Check: test seams and scenario testability. **CONFIRMED.**

### 📌 Suggestions

6. **A 1 px inset can hide a cell cut off to a few minutes at an axis end, and percent-positioned blocks may not suit the later cloud agreement band (#186).** Check: risks. The first part is **CONFIRMED**. The second is **OUT-OF-SCOPE**: #186 can draw its band per hour inside each cell, or rework the row when it is planned.
7. **Plain language: long sentences, actorless passives, and two words for one concept ("blank cell" and "no cell"; "band" and "step"; "tick" and "time label").** Check: plain language. **CONFIRMED** for the spec, design, proposal and ledger.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD5: pin the locale `en-GB` and `numberingSystem: "latn"`. specs: "The strip shows times in Home Assistant's time zone" requires the digits `0` to `9`, with an `ar-EG` scenario.
2. design.md DD7 and specs "The strip spans the judged night": fall back when `end` is not after `start`, or when the two are more than 48 hours apart; add a scenario for an inverted window. DD6 states the resulting loop bound.
3. specs: a new requirement, "The axis carries time labels": labels strictly inside the axis, every 6 hours on an axis over 24 hours, one label when clocks go back; scenarios for polar night and Athens. design.md DD6 says how; DD9 asks a sections dashboard for the full width; DD2 centres a label on its instant. brainstorm.md D11 carries the 6-hour rule.
4. design.md DD7 and specs: an `unavailable` cloud sensor gives an empty row even with a `forecast`; add that scenario.
5. design.md Test Seams and Blast radius, and proposal.md Impact: name `tests/test_night_card_doc.py`. specs: the docs scenario asserts all six topics.
6. design.md DD2, DD3 and Risks: no inset on a clipped edge, so an end cell stays flush and visible; cells carry their drawn bounds in `data-from` and `data-to`. specs: "A value fills its hour" says a cut-off cell reaches the axis end with no gap.
7. Plain language: split the long requirement sentences and turn passives active in specs; use "blank hour", "shade step" and "time label" throughout brainstorm.md (D6, D8, D14), proposal.md, specs and design.md.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1.
2. Fixed: required change 2.
3. Fixed: required change 3.
4. Fixed: required change 4.
5. Fixed: required change 5.
6. First part fixed: required change 6. Second part declined: the cloud agreement band (#186) is a later story, and DD1 keeps the strip model separate from its markup, so that story can choose its own drawing.
7. Fixed: required change 7. The ADR manifest's summary sentence is left as it is: it lists the decisions it rejected and reads as a list.
