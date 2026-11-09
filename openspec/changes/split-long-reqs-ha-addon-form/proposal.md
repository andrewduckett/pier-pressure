## Why

Two requirements in `ha-addon`, about the Configuration form and how it combines with `config.yaml`, run to 2,572 and 3,710 characters, and each bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 1 of 3 for `ha-addon` in epic #230.

## What Changes

- Split "The add-on offers a Configuration form for the interval and piers" into seven requirements: the three top-level settings, the broker block, a pier's horizon fields, its equipment fields, its gate fields, the names that match `config.yaml`, and the English labels (D3).
- Split "The add-on combines the Configuration form with config.yaml" into eighteen requirements, one for each rule and each case that stops the add-on (D4).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D8).
- Every existing scenario moves word for word, and every SHALL, SHALL NOT and MAY keeps its meaning (D7).
- Add five scenarios, one for each split-out behavior that has none of its own. Each restates SHALLs its new requirement keeps, and an existing test already asserts it (D5).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: two long requirements become 25 requirements with the same meaning, and five scenarios are added.

## Impact

- Spec text only: `openspec/specs/ha-addon/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D2).
- The added scenarios restate behavior that existing tests already assert, so no test changes (D5).
- No requirement was found to disagree with the code (D6).
- The 8 other long `ha-addon` requirements stay for #238 and #239 (D1).
