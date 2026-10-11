## 1. The add-on manifest and its labels

- [ ] 1.1 Write failing tests in `tests/test_ha_addon.py` (design D4, D5). Extend the schema test: each pier item has `equipment_focal_length_mm`, `equipment_sensor_width_mm`, `equipment_sensor_height_mm` and `equipment_reducer`, each `float(0,)?`, and `options` sets none of them. Verify they fail.
- [ ] 1.2 Add the four fields to the pier schema in `ha-addon/config.yaml`, with a comment naming this change's D4. Add their names and descriptions under `piers.fields` in `ha-addon/translations/en.yaml` (design D5). Verify the 1.1 tests pass, and that the existing label test covers all four new fields.

## 2. Turning the form fields into equipment

- [ ] 2.1 Write failing tests in `tests/test_addon_options.py` for `read_addon_options` (design D1 to D3):
  - All four fields become `equipment: {focal_length_mm, sensor_width_mm, sensor_height_mm, reducer}`.
  - Three fields without the reducer give a block without `reducer`.
  - Only some fields give a block with just those keys, for the core to reject.
  - A pier with no equipment field has no `equipment` key.
  - A field saved as `null` counts as unset, and all four `null` give no `equipment` key.
  - A pier with both an `equipment` key and an `equipment_*` field is left out, and the log names the pier and `equipment`.
  - An `equipment` key on its own passes through unchanged.
  - The horizon fields still become a `horizon` block beside the `equipment` block.

  Verify they fail.
- [ ] 2.2 Change `pierpressure/addon_options.py` to rebuild each pier's `equipment` block, and update its module and function docstrings to name equipment beside the horizon. Verify the 2.1 tests and the existing tests in the file pass.

## 3. Equipment from the form, end to end

- [ ] 3.1 Write failing tests in `tests/test_main.py` for `load_app_config`. Use a temporary `options.json` inside an add-on, and cover each scenario in the requirement "The form sets each pier's equipment":
  - four values give the same equipment as a `config.yaml` pier with the same `equipment` block
  - no reducer gives a reducer of 1.0
  - no equipment fields give no equipment
  - saved `null` values count as unset, and a `null` required field skips the pier, naming `sensor_height_mm`
  - a missing sensor height, and a reducer alone, each skip only their pier and name the missing key
  - 0 and −1 in each of the four fields skip only their pier and name the key (parameterized)
  - an `equipment` mapping beside an equipment field skips only its pier and names `equipment`
  - incomplete equipment on the only pier stops the add-on with "No valid pier"

  Verify any that fail, and fix the code until they pass.
- [ ] 3.2 Write a test that a form pier and a `config.yaml` pier rank alike. Use the pinned instant, conditions and London pier of `test_an_equipped_pier_emits_an_equipment_reason_for_the_top_pick` in `tests/test_producer_targets.py`. Give both piers the same id, location, elevation, horizon and four equipment values. Verify both produce the same verdict JSON, that its top pick has a known size, and that `reasons[]` holds exactly one field-of-view sentence for that top pick.
- [ ] 3.3 Run `just check` and verify that it is green.

## 4. Documentation

- [ ] 4.1 Update `ha-addon/DOCS.md`. Describe the four equipment fields, with an example, and say the three sizes go together and an empty reducer means 1.0. List each form label beside its `config.yaml` name, such as "Sensor height" and `equipment.sensor_height_mm`, so a user can match a log line to a field. Remove equipment from any list of settings only `config.yaml` can hold. Verify by reading the rendered Markdown.
- [ ] 4.2 Update the README's add-on section in `README.md` to match 4.1. Verify that it no longer sends a form user to `config.yaml` for equipment.

## 5. Live check

- [ ] 5.1 The maintainer checks the form on a real Home Assistant OS instance, with an add-on built from this branch, as in addon-options-form task 6.1. Record the Home Assistant and Supervisor versions in the PR, with the result of each of the four pass conditions in the design's risks section. If no instance is available before merge, record that the check is still open.
