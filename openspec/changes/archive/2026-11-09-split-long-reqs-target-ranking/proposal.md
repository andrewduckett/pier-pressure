## Why

Five requirements in `target-ranking` each run past 500 characters, and each bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story applies the pattern that the pilot (#231) proved to the next spec in epic #230.

## What Changes

- Split "Targets are gated before ranking" into three requirements (D4).
- Split "Each target carries its computed observing geometry" into four requirements, and add one scenario to each of two of them (D5).
- Split "Targets are scored and ordered deterministically" into nine requirements, and add one scenario to one of them (D6).
- Split "Each target carries its size and brightness" into two requirements, and add one scenario to one of them (D7).
- Split "The verdict says how the top pick frames" into five requirements: one for when the framing sentence is added, and one for each of the four sentences (D8).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D11).
- Every existing scenario moves word for word, and every SHALL, SHALL NOT and MAY keeps its meaning (D3, D10). The four added scenarios each restate a SHALL the new requirement keeps.
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `target-ranking`: five long requirements become 23 requirements with the same meaning, and four scenarios are added.

## Impact

- Spec text only: `openspec/specs/target-ranking/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- Each added scenario restates behavior that an existing test already asserts, so no test changes (D3).
- The framing-sentence requirement disagrees with the code in two ways: the code adds a brightness sentence the spec does not name, and withholds the top-pick sentences when the scored window is under an hour. This change keeps the requirement's meaning and reports the drift (D9).
