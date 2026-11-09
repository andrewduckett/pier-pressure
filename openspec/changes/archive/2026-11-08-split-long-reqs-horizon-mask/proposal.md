## Why

Five requirements in `horizon-mask` each run past 500 characters, and four of them bundle several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story applies the pattern that the pilot (#231) proved to the next spec in epic #230.

## What Changes

- Split "Canonical horizon representation" into six requirements, and add one scenario to each of two of them (D4).
- Split "Inline points configuration" into six requirements, and add one scenario to one of them (D5).
- Split "NINA horizon import" into five requirements (D6).
- Split "Flat floor and default open sky" into three requirements (D7).
- Restate "The horizon does not change the verdict document" as one shorter requirement under a new heading, with the same meaning (D8, D9).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D11).
- Every existing scenario moves word for word, and every SHALL and MAY keeps its meaning (D3, D10). The three added scenarios each restate a SHALL the new requirement keeps.
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `horizon-mask`: five long requirements become 21 requirements with the same meaning, and three scenarios are added.

## Impact

- Spec text only: `openspec/specs/horizon-mask/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- Each added scenario restates behavior that an existing test already asserts, so no test changes (D3).
- The verdict-document requirement disagrees with the code and with `target-ranking` about `targets`. This change keeps that requirement's meaning and reports the drift for a separate bug (D9).
