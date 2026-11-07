## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon through the t3 resolver). `lets delegate` timed out after 900000 ms and left the raw file empty; the review had finished in its thread, `7541184a-f424-4130-a2f9-0d33b5b04fa3`, and its final message was recovered as the raw file.
- **Independent**: yes. The plan's author is the claude family.
- **Tool restrictions**: read-only (plan mode: view, grep, glob only)
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `d4ea783`

## Findings

### 🔴 Critical (blocking)

1. **`ha-form` ignores a `label` on the schema entry, so the field would read `pier`, not **Pier**.** Check: contradictions (design D-3 against "The card has a visual editor"); test seams (the stand-in would hide it). `ha-form` takes labels from its `computeLabel` callback and falls back to the schema's `name`. CONFIRMED: Home Assistant's own card editors pass `computeLabel`; the schema type has no `label`.
2. **Clearing the field sends `pier: undefined`, which D-3's string check drops.** Check: contradictions (D-3's "an emptied field reports `pier: ""`"). Home Assistant's select selector forwards `undefined` from the clear button, so the configuration would stay on the old pier. CONFIRMED: D-3 named only a string as a change.
3. **Adding an unlisted `config.pier` to `options` breaks "No other entity SHALL add a pier", and lists one pier twice when PierPressure is offline.** Check: contradictions; a failure mode the author did not list. Offline, the Verdict sensor loses its attributes, so the list holds `back_yard` while the configuration holds `Back-Yard`, and both would show. Home Assistant's combo box already shows a value that is not in its options. CONFIRMED.

### 🟡 Moderate

4. **The closed combo box shows the stored value (`dong_jing`), not the label (`東京`), and `mode: "dropdown"` does nothing with `custom_value`.** Check: contradictions (D-3's "shows the label of the current value"). CONFIRMED. The spec only requires the list to show labels, so no requirement changes.
5. **Assumption D11 and the starting-configuration requirement say the picker's preview shows "pier is required".** Check: assumption rows; scenario testability. The picker shows the entry's description when the card throws; the error shows only in the edit dialog's preview, and no scenario asserted it. CONFIRMED.
6. **`tests/test_night_card_doc.py` is missing from the test seams and impact, and D-7 adds a troubleshooting entry no spec asks for.** Check: test seams; scope. The main spec's "The docs say what to do when something is missing" lists that section's entries. CONFIRMED.

### 📌 Suggestions

7. **D-1 does not say that an `undefined` entry in `hass.states` is skipped.** Check: contradictions with the `HomeAssistant` type in `card/src/pierpressure-card.ts`. Accepted.
8. **`mise run dashboard-check`'s two dashboards are in YAML mode, so the by-eye check needs the Overview dashboard; three sentences break plain language (one passive SHALL that hides the actor, and sentences over 30 words in design.md and adr.md).** Check: plain language; test seams. Accepted. `scripts/dashboard_check.py` sets `mode: yaml` on both dashboards.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

The reviewer suggested REVISE. Every Critical and Moderate finding is fixed by a small, unambiguous edit listed below, and no finding is left open, so the verdict is APPROVE_WITH_CHANGES.

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md D-3: drop the schema `label`; pass `computeLabel` returning **Pier**. Test Seams: the stand-in `ha-form` shows labels from `computeLabel`. (Finding 1)
2. design.md D-3: treat a cleared field's `undefined` as `""`, and report it when it differs from the current `pier`. (Finding 2)
3. design.md D-3: `options` are exactly `listPiers(hass.states)`; pass `data.pier` as the configured string, or `""`; never add options. (Finding 3)
4. design.md D-3: say the closed field shows the stored value and the open list shows labels; drop `mode: "dropdown"`. (Finding 4)
5. spec.md "The card offers a starting configuration": drop the preview clause. brainstorm.md D11: say the picker shows the description, and the edit dialog's preview shows "pier is required". design.md Context: note the picker's fallback. (Finding 5)
6. design.md Test Seams and Blast radius, and proposal.md Impact: add `tests/test_night_card_doc.py`. design.md D-7: leave "If something looks wrong" unchanged. (Finding 6)
7. design.md D-1: skip entries whose entity is `undefined`. (Finding 7)
8. design.md Test Seams and brainstorm.md D14: the by-eye check uses the Overview dashboard at `/lovelace`. spec.md "The card has a visual editor": "The editor SHALL report each change". Split the long sentences in design.md Context and Risks, and in adr.md's summary. (Finding 8)

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md D-3 (`computeLabel`) and Test Seams (stand-in reads `computeLabel`).
2. Fixed: design.md D-3, "Clearing the field gives `undefined`, which the editor treats as `""`".
3. Fixed: design.md D-3, "Its `options` are exactly `listPiers(hass.states)`" and the `data` line.
4. Fixed: design.md D-3, the closed-field paragraph; `mode: "dropdown"` removed.
5. Fixed: spec.md starting-configuration requirement; brainstorm.md D11; design.md Context, first API bullet.
6. Fixed: design.md Test Seams ("Docs seam") and Blast radius; proposal.md Impact; design.md D-7.
7. Fixed: design.md D-1.
8. Fixed: design.md Test Seams; brainstorm.md D14; spec.md visual editor requirement; design.md Context and Risks; adr.md Review Summary.
