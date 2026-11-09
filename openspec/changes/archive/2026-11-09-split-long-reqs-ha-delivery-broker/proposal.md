## Why

Six `ha-delivery` requirements about the broker connection run to between 541 and 3,342 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 1 of 2 for `ha-delivery` in epic #230; #241 splits the rest.

## What Changes

- Split "Persistent operation with periodic republish" into two requirements (D3), "Availability reflects process liveness via last-will" into five (D4), "Delivery failures are reported, not swallowed" into five (D5), "The process waits for the broker at startup" into seven (D6), "The process restores delivery after a reconnect" into ten (D7) and "An error about the broker settings shows none of their text" into four (D8). That makes 33 ADDED requirements.
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D14).
- Two unquoted pointers, "the reconnect requirement" and "the startup requirement", become quoted pointers to the new requirements they mean (D10).
- Every existing scenario moves word for word. One scenario is added, so the new requirement on held publishes has one (D9). Every SHALL, SHALL NOT and MAY keeps its meaning. One descriptive sentence becomes a SHALL NOT that its scenario already asserts (D13).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: six long requirements become 33 requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/ha-delivery/spec.md` after archive.
- No spec quotes a heading this change removes (D10).
- Three test docstrings restate a removed heading: `tests/test_broker_wait.py:1`, `tests/test_reconnect.py:1` and `tests/test_service_reconnect.py:1`. They stay as they are, because the epic changes no code or test. The pull request lists them (D11).
- No requirement was found to disagree with the code (D12).
- The other long `ha-delivery` requirements stay for #241, so `ha-delivery` still has long-requirement warnings after this change (D15).
