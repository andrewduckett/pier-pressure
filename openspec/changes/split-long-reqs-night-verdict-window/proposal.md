## Why

Six `night-verdict` requirements about the night window, the scored span, the moon and offline astronomy run to between 924 and 3,315 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 1 of 3 for `night-verdict` in epic #230.

## What Changes

- Split "The verdict judges the remaining night" into ten requirements (D3), "Night window is the astronomical-night boundary" into six (D4), "Reasons name the scored span" into three (D5), "Conditions are evaluated across the whole scored window" into four (D6), "Moon information across the dark window" into three (D7) and "Astronomical fields are computed offline with stable precision" into three (D8). That makes 29 ADDED requirements.
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D14).
- Every existing scenario moves word for word. Five scenarios are added, one for each new requirement that no original scenario fits, and each rests on an existing test (D9).
- Every SHALL and SHALL NOT keeps its meaning. Four SHALL are added without adding an obligation: three descriptive sentences become SHALL statements so each new requirement has one, and one field list is split in two (D13).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: six long requirements become 29 requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/night-verdict/spec.md` after archive.
- No spec quotes a heading this change removes (D10).
- No code, test, card, doc or README text quotes a removed heading. Three comments echo one without quoting it, and stay as they are: `pierpressure/core/sky.py:12`, `tests/test_sky_dark_window.py:1` and `card/src/pierpressure-card.ts:588` (D11). The pull request lists them.
- One drift: at the exact poles the code anchors continuous polar night to the UTC calendar day, where the text says the local solar day. The text keeps its meaning, and the REMOVED Reason and the pull request note it (D12).
- After archive, `night-verdict` still has 14 long-requirement warnings. #243 and #244 split those (D15).
