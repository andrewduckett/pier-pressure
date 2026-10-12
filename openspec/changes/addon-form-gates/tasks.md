## 1. The add-on manifest and its labels

- [x] 1.1 Write failing tests in `tests/test_ha_addon.py` (design D2, D4). Extend the schema test: each pier item has `go_threshold: int(0,100)?` and `max_gust: float(0,)?`, and `options` sets neither. Add both fields to the unit test: `go_threshold` says "no unit" and `max_gust` says "km/h". Add a test that their descriptions say what an empty field means: 65 for `go_threshold`, and no wind gate for `max_gust`. Verify they fail.
- [x] 1.2 Add the two fields to the pier schema in `ha-addon/config.yaml`, with a comment naming this change's D2. Add their names and descriptions under `piers.fields` in `ha-addon/translations/en.yaml` (design D4). Verify the 1.1 tests pass, and that the existing label test covers both new fields.

## 2. Leaving out an unset gate field

- [x] 2.1 Write failing tests in `tests/test_addon_options.py` for `translate_form` (design D1):
  - `go_threshold` 75 and `max_gust` 40 pass through unchanged.
  - `go_threshold` 0 passes through, because 0 counts as set.
  - Each field absent, saved as `null`, empty text or blank text is left out (parameterized).
  - A bad value, such as `max_gust` 0, passes through for the core to reject.

  Verify the `null` and blank-text cases fail.
- [x] 2.2 Change `pierpressure/addon_options.py` to leave out each unset gate field, with the two names in one constant beside `HORIZON_FIELDS` and `EQUIPMENT_FIELDS`. Update its module and `translate_form` docstrings to name the gate fields. Verify the 2.1 tests and the existing tests in the file pass.
- [x] 2.3 Write a test in `tests/test_addon_options.py` that guards the risk in the design: for each optional pier field in the manifest's schema, a pier with that field saved as `null` translates to a pier without that field, or without the block it builds. Verify it passes.

## 3. The gate fields from the form, end to end

- [ ] 3.1 Write tests in `tests/test_main.py` for `load_app_config`. Use a temporary `options.json` inside an add-on, and cover each scenario in the requirement "The form sets each pier's GO threshold and wind-gust limit":
  - empty fields (absent, `null`, blank text) give a checked pier with a `go_threshold` of 65 and no `max_gust`
  - `config.yaml` fills a `max_gust` saved as `null`, with no "set in both places" error
  - a `go_threshold` set on the form and in `config.yaml` stops the add-on, naming `go_threshold` and `backyard`
  - `max_gust` 0 and `go_threshold` 101 each skip only their pier, and the log names the pier and the field
  - a bad value on the only pier stops the add-on with "No valid pier"

  Verify any that fail, and fix the code until they pass.
- [ ] 3.2 Write a test that a form pier and a `config.yaml` pier get the same verdict, with `go_threshold` 75 and `max_gust` 40. Use a pinned instant and fixed conditions, following `tests/test_verdict_eval.py`. Verify both produce the same verdict JSON.
- [ ] 3.3 Write a test that a form pier with `max_gust` 30 gets a `NO-GO` when the conditions hold a 45 km/h gust in the dark window and no other gate fails. Verify the score is null and `reasons[]` names the 30 km/h limit.
- [ ] 3.4 Run `just check` and verify that it is green.

## 4. Documentation

- [ ] 4.1 Update `ha-addon/DOCS.md`. Describe the two fields with the other pier fields: their range, their unit, and what an empty field means. List each form label beside its `config.yaml` name. In the list of what `config.yaml` can add, replace `go_threshold` and `max_gust` with other examples, such as a horizon file and `explainer`. Verify by reading the rendered Markdown.
- [ ] 4.2 Update the README's add-on section in `README.md` to match 4.1. Verify that it no longer sends a form user to `config.yaml` for these two settings.

## 5. Live check

- [ ] 5.1 The maintainer checks the form on a real Home Assistant OS instance, with an add-on built from this branch, as in addon-options-form task 6.1. Check that the form shows both fields empty; refuses a `go_threshold` of 101 and a negative `max_gust` on save; accepts a `go_threshold` of 0 and 100 and a `max_gust` of 0; and that clearing a field saves without error. Record the Home Assistant and Supervisor versions in the PR, with each result. If no instance is available before merge, record that the check is still open.
