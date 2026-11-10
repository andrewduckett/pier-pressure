## Why

Four `ha-addon` requirements cover the Configuration form's field groups: a pier's horizon, its equipment, its GO threshold and wind-gust limit, and the broker. They run to between 1,132 and 1,726 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 2 of 3 for `ha-addon` in epic #230.

## What Changes

- Split "The form sets each pier's horizon" into six requirements (D3), "The form sets each pier's equipment" into six (D4), "The form sets each pier's GO threshold and wind-gust limit" into four (D5) and "The form sets the broker" into six (D6).
- The rule that the add-on stops when every pier is skipped appears in three of the four requirements. It becomes one shared requirement (D7). That makes 23 ADDED requirements in all.
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D14).
- Three pointers to "The add-on combines the Configuration form with config.yaml", a heading #237 removed, now name the requirement that holds the rule (D8).
- MODIFY "The add-on uses the Supervisor's MQTT broker when the settings name none" only to retarget its two pointers, so no pointer names a heading this change removes. Its other text and scenarios stay word for word (D9).
- Every existing scenario moves word for word, no scenario is added (D11), and every SHALL and SHALL NOT keeps its meaning (D13).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: four long requirements become 23 requirements with the same meaning, and one requirement's pointers are retargeted.

## Impact

- Spec text only: `openspec/specs/ha-addon/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes (D9).
- No requirement was found to disagree with the code (D12).
- The 4 other long `ha-addon` requirements stay for #239. Three of their pointers still name the heading #237 removed. The pull request names them, so #239 can retarget them when it splits those requirements (D10).
