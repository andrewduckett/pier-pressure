## Why

Nine requirements in `conditions` each run past 500 characters, and each bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story applies the pattern that the pilot (#231) proved to the next spec in epic #230.

## What Changes

- Split "Cloud cover carries a low/mid/high component split" into three requirements (D4).
- Split "Each fetch reports its outcome per provider" into eight requirements (D5).
- Split "A failed computed outcome says which input was missing" into four requirements: one for when the outcome carries an error and how its parts are joined, and one for each fixed reason (D6).
- Split "Each variable is filled from the first provider in order that returned it" into two requirements (D7).
- Split "The computed source reports an outcome like a provider" into four requirements (D8).
- Split "The snapshot keeps alternates beside the filled series" into three requirements (D9).
- Split "NWS periods are expanded onto the hourly grid within a 72-hour horizon" into three requirements (D10).
- Split "Each Open-Meteo model declares the variables its model returns" into four requirements (D11).
- Split "Every Open-Meteo request asks for the 4 hours before the fetch and the 72 after" into two requirements, and add one scenario to the second (D12).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D15).
- Every existing scenario moves word for word, and every SHALL and SHALL NOT keeps its meaning (D3, D14). The one added scenario restates a SHALL its new requirement keeps.
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: nine long requirements become 33 requirements with the same meaning, and one scenario is added.

## Impact

- Spec text only: `openspec/specs/conditions/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- The added scenario restates behavior that an existing test already asserts, so no test changes (D3, D12).
- No requirement was found to disagree with the code (D13).
