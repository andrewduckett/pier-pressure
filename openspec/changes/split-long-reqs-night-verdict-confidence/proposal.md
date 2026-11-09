## Why

Eight `night-verdict` requirements about confidence, cloud agreement and the hourly timeline run to between 530 and 923 characters, and seven of them bundle several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. They are the last long-requirement warnings in any main spec. This story is part 3 of 3 for `night-verdict` in epic #230.

## What Changes

- Split "Confidence is present and banded" into four requirements (D3), "The document carries an hourly timeline" into three (D4), "A timeline entry has a fixed flat shape" into two (D5), "The document carries cloud agreement" into two (D6), "Cloud agreement is the clarity-weighted mean gap over the scored window" into three (D7), "Confidence falls with low agreement" into four (D8) and "Reasons name the agreement" into two (D9).
- "Variables the timeline does not show never change the document" states one behavior, so it becomes one new requirement with tighter wording (D10).
- That makes 21 ADDED requirements. Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D16).
- Every existing scenario moves word for word. One scenario is added, for the new requirement that no original scenario fits. An existing test backs it (D11).
- Every SHALL and SHALL NOT keeps its meaning, and the count stays at 33 (D15).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: eight long requirements become 21 requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/night-verdict/spec.md` after archive.
- No spec quotes a heading this change removes (D12).
- Three test section comments quote a removed heading, and one quotes a shortened form. They stay as they are, and the pull request lists them (D13).
- No drift between the 8 requirements and the code was found (D14).
- After archive, no main spec has a long-requirement warning. That lets #245 add `openspec validate --specs --strict` to `mise run check` (D17).
