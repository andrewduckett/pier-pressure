## Why

Seven requirements in `night-card` each bundle several behaviors in more than 500 characters (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story applies the pattern that the pilot (#231) proved to the next spec in epic #230.

## What Changes

- Split "The card draws the four cloud rows" into three requirements, and add one scenario for each of two of them (D4).
- Split "The strip spans the judged night" into three requirements (D5).
- Split "The card draws every timeline row" into two requirements (D6).
- Split "A missing sensor leaves its row empty" into two requirements (D7).
- Split "A Cloud range row with no column says why" into three requirements, and add one scenario to one of them (D8).
- Split "The docs describe the Cloud range row" into two requirements, and add one scenario to one of them (D9).
- Split "The strip stays where the user panned it" into six requirements, one per behavior (D10).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D12).
- Every existing scenario moves word for word, and every SHALL keeps its meaning (D3, D11). The four added scenarios each restate a SHALL the new requirement keeps.
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: seven long requirements become 21 requirements with the same meaning, and four scenarios are added.

## Impact

- Spec text only: `openspec/specs/night-card/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- Each added scenario restates behavior that an existing test already asserts, so no test changes (D3).
