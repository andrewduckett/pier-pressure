## 1. The add-on manifest and its labels

- [x] 1.1 Write failing tests in `tests/test_ha_addon.py` (design D4, D5). Extend the schema test: each pier item has `min_altitude: float(0,90)?` and an optional `match(...)` type for `horizon_points`, and `options` does not set either field. Add a test that reads the `horizon_points` pattern from the manifest and applies it with `re.match`, as the Supervisor does. It accepts `[[0, 10], [90, 25]]`, empty text and blank text. It rejects `[0, 10], [90, 25]` and `[[0, 10]] extra`. Verify they fail.
- [x] 1.2 Add both fields to the pier schema in `ha-addon/config.yaml`, with a comment naming this change's D4. Add their names and descriptions under `piers.fields` in `ha-addon/translations/en.yaml` (design D5). Verify the 1.1 tests pass, and that the existing label test covers both new fields.

## 2. Turning the form fields into a horizon

- [x] 2.1 Write failing tests in `tests/test_addon_options.py` for `read_addon_options` (design D1 to D3):
  - `min_altitude` becomes `horizon: {min_altitude: ...}`.
  - `horizon_points` text becomes `horizon: {points: [...]}`.
  - A pier with neither field has no `horizon` key.
  - Blank or empty `horizon_points` counts as unset.
  - Both fields set give a `horizon` block with both keys.
  - Text that is not valid YAML leaves that pier out and logs an error naming the pier and `horizon_points`.
  - A `horizon_points` value that is not text leaves that pier out and logs an error naming `horizon_points`.
  - A pier entry that is not a mapping passes through unchanged.
  - When every pier is left out, the result still holds an empty `piers` list, not `None`.

  Verify they fail.
- [x] 2.2 Change `pierpressure/addon_options.py` to rebuild each pier's `horizon` block, and update its module and function docstrings. They must no longer say that pier entries pass through unchanged. Verify the 2.1 tests and the existing tests in the file pass.

## 3. The horizon from the form, end to end

- [ ] 3.1 Write failing tests in `tests/test_main.py` for `load_app_config`. Use a temporary `options.json` inside an add-on, and cover each scenario in the requirement "The form sets each pier's horizon":
  - a flat floor of 15
  - points equal to a `config.yaml` pier with the same `horizon.points`
  - no fields means open sky
  - a blank points field beside a floor
  - unreadable text, a non-text value, an out-of-range point, and both fields set each skip only their pier
  - a bad horizon on the only pier stops the add-on with "No valid pier"

  Verify any that fail, and fix the code until they pass.
- [ ] 3.2 Run `just check` and verify that it is green.

## 4. Documentation

- [ ] 4.1 Update `ha-addon/DOCS.md`. Describe the two horizon fields, with a one-line points example, and say they cannot be used together. Remove the horizon from the list of settings only `config.yaml` can hold, but keep horizon files on it. Verify by reading the rendered Markdown.
- [ ] 4.2 Update the README's add-on section in `README.md` to match 4.1. Verify that it no longer sends a form user to `config.yaml` for a flat floor or points.

## 5. Live check

- [ ] 5.1 The maintainer checks the form on a real Home Assistant OS instance, with an add-on built from this branch, as in addon-options-form task 6.1. Record the Home Assistant and Supervisor versions, and the result of each pass criterion in the design's risks section, in the PR. If no instance is available before merge, record that the check is still open.
