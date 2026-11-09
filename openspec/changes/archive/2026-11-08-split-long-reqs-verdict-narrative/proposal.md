## Why

Four requirements in `verdict-narrative` each bundle several behaviors in more than 500 characters (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story applies the pattern that the pilot (#231) proved to the next spec in epic #230.

## What Changes

- Split "Narrative explains an already-computed verdict" into two requirements, one per behavior (D3).
- Split "Narratives are cached on the deterministic verdict terms" into two requirements (D4).
- Split "An error about the explainer settings shows none of their text" into five requirements, one per kind of input (D5).
- Split "The explainer degrades gracefully on failure" into two requirements, and add one scenario for its timeout edge case, so each new requirement has a scenario (D6).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires.
- Every existing scenario moves word for word, and every SHALL keeps its meaning (D7, D8).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `verdict-narrative`: four long requirements become eleven requirements with the same meaning, and one scenario is added.

## Impact

- Spec text only: `openspec/specs/verdict-narrative/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- The added scenario restates behavior that existing tests already cover, so no test changes.
