## 1. The core reads horizon points written as text

- [x] 1.1 Write failing tests in `tests/test_horizon_config.py` (design D1, D6), each through `validate_piers` beside a valid second pier:
  - `horizon.points` as the text `"[[0, 10], [90, 25], [180, 5]]"` gives the same horizon as the same list
  - the text `"[[0, 10], [90"` skips its pier; the logged error names `horizon.points`, and the YAML reader's message in it holds no line break
  - the texts `"5"`, `"{a: 1}"`, `""`, `"   "` and `"# none"` each skip their pier, with `horizon.points` in the logged error
  - the other pier still validates in every case

  Verify that the text cases fail.
- [x] 1.2 In `pierpressure/core/config.py`, add a `field_validator("points", mode="before")` to `HorizonConfig`. It parses text with `yaml.safe_load`, raises `ValueError` when the YAML is invalid (with the reader's message on one line) or parses to `None`, and passes any other value through. Update the class docstring. Verify the 1.1 tests and the existing tests in `tests/test_horizon_config.py` and `tests/test_config.py` pass.

## 2. The add-on renames the horizon fields and nothing more

- [x] 2.1 Write failing tests in `tests/test_addon_options.py` (design D2, D6):
  - `horizon_points` text passes through unchanged as `horizon.points`
  - a number in `horizon_points` passes through unchanged as `horizon.points`
  - a pier with a `horizon` mapping and a set `horizon_points` keeps the mapping and `horizon_points` unchanged
  - a pier with a `horizon` mapping, blank `horizon_points` and a null `min_altitude` keeps the mapping and loses both flat fields

  Verify that they fail.
- [x] 2.2 Rewrite `_with_horizon_block` in `pierpressure/addon_options.py` as design D2 describes: drop unset horizon fields; when `horizon` is set, leave the set fields in place; otherwise rename them without parsing. Remove the tests for the two `horizon_points` errors and the one-line YAML log. Verify the 2.1 tests and the remaining tests in `tests/test_addon_options.py` pass.

## 3. The equipment fields follow the same rule

- [ ] 3.1 Write failing tests in `tests/test_addon_options.py` (design D3, D6):
  - a pier with an `equipment` mapping and a set `equipment_focal_length_mm` keeps both unchanged, and nothing is logged
  - a pier with a complete `equipment` mapping and a null `equipment_focal_length_mm` keeps the mapping and loses the null field

  Verify that they fail.
- [ ] 3.2 Rewrite `_with_equipment_block` as design D3 describes, so it no longer raises. Remove the test for the `equipment` conflict error. Verify the 3.1 tests and the existing null-`equipment` test pass.

## 4. The translation keeps every pier

- [ ] 4.1 Make `_config_piers` stop catching `ValueError`, and remove the imports and `logger` that nothing uses any more (design D4). Remove the test that expects an empty list after every pier is skipped. Update the docstrings of the module, `translate_form`, `_config_piers` and `_merge`, and the module docstring of `pierpressure/addon_settings.py`, so they no longer describe a pier the translation skipped. Verify the tests in `tests/test_addon_options.py` and `tests/test_addon_settings.py` pass, and that `uv run ruff check` reports no unused import.

## 5. End to end through the add-on

- [ ] 5.1 Write tests in `tests/test_main.py` or `tests/test_addon_settings.py` that run the saved form values through `combine_settings` and the core (design D6, the `ha-addon` delta):
  - piers with a latitude of 95, a `go_threshold` of 101 and a `horizon_points` of 5 each skip with an error that names the same setting as the error for a `config.yaml` pier with the same value; a fourth pier validates
  - an `equipment` mapping beside `equipment_focal_length_mm` skips the pier with an error that names `equipment_focal_length_mm`, and the add-on logs no error of its own
  - a `horizon` mapping beside `horizon_points` skips the pier with an error that names `horizon_points`
  - a form pier whose `horizon_points` is `[[0, 10], [90` still counts as listed when `config.yaml` sets its `go_threshold`; the error names `horizon.points`

  Verify they pass.

## 6. Documentation

- [ ] 6.1 Add one line to the "Set a pier's horizon" section of `ha-addon/DOCS.md`: an error about `horizon.points` refers to the form's `horizon_points` field. Verify the add-on docs tests pass.
- [ ] 6.2 Check that ADR-0022 is in `docs/decisions/` and that its status is `accepted`.

## 7. Check

- [ ] 7.1 Run `just check` and verify that it is green.
