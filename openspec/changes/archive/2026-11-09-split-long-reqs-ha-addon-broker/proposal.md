## Why

The last four long `ha-addon` requirements cover the Supervisor's broker, the wait for it, the add-on's config folder and how saved settings are checked. They run to between 856 and 1,502 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 3 of 3 for `ha-addon` in epic #230, so it leaves that spec with no long-requirement warning.

## What Changes

- Split "The add-on reads config from its own config folder" into three requirements (D3), "The add-on uses the Supervisor's MQTT broker when the settings name none" into seven (D4), "The add-on waits a bounded time for the Supervisor's broker" into four (D5) and "The core checks every saved setting" into four (D6). That makes 18 ADDED requirements.
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D13).
- Three pointers to "The add-on combines the Configuration form with config.yaml", a heading #237 removed, now name a requirement that still exists (D8).
- MODIFY "A broker host on the form sets all four connection settings" only to retarget its pointer, so no pointer names a heading this change removes. Its other text and scenarios stay word for word (D9).
- Every existing scenario moves word for word. Two scenarios are added, so each requirement split from "The core checks every saved setting" has one (D7). Every SHALL, SHALL NOT and MAY keeps its meaning (D12).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: four long requirements become 18 requirements with the same meaning, and one requirement's pointer is retargeted.

## Impact

- Spec text only: `openspec/specs/ha-addon/spec.md` after archive.
- Two code comments name a heading that no longer exists: one in `pierpressure/supervisor.py` names a heading this change removes, and one in `tests/test_addon_settings.py` names the heading #237 removed. They stay as they are, because the epic changes no code or test. The pull request names them (D10).
- No requirement was found to disagree with the code (D11).
- After this change, `ha-addon` has no long-requirement warning (D14).
