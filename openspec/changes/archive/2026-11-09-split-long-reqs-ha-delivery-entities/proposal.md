## Why

Eight `ha-delivery` requirements about the published entities run to between 547 and 3,447 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 2 of 2 for `ha-delivery` in epic #230, so it must leave the spec with no long-requirement warning.

## What Changes

- Split "Per-pier entity auto-discovery" into two requirements (D3), "Verdict state and attributes are exposed" into three (D4), "Top target is exposed as an entity" into four (D5), "Narrative is exposed as an optional entity" into seven (D6), "Each rank of the target list is exposed as an entity" into five (D7), "Provider health is exposed as diagnostic entities" into twelve (D8), "The Cloud cover state is the current hour's value" into two (D9) and "Each further timeline variable is exposed as an entity" into two (D10). That makes 37 ADDED requirements.
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D16).
- Every existing scenario moves word for word. Four scenarios are added, one for each new requirement that no original scenario fits (D11). Every SHALL and SHALL NOT keeps its meaning. One "SHALL carry" is repeated three more times, because one attribute list becomes four requirements (D15).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: eight long requirements become 37 requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/ha-delivery/spec.md` after archive.
- No spec quotes a heading this change removes (D12).
- No code, test, card, doc or README text quotes a removed heading (D13). Three lines describe a sensor's state as "the current hour's value", which echoes one removed heading without quoting it: `tests/test_timeline_sensors.py:4`, and `pierpressure/delivery/mqtt.py:416` and `:476`. They stay as they are, because the epic changes no code or test. The pull request lists them.
- No requirement was found to disagree with the code (D14).
- After archive, `ha-delivery` has no long-requirement warning (D17).
