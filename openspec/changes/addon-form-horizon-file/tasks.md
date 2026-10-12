## 1. A file reader that keeps file content out of errors

- [x] 1.1 Write failing tests in `tests/test_config.py` for a new `read_config_mapping` (design D4). It returns the parsed, `${VAR}`-expanded mapping without building a `ConfigFile`, so a file that sets `mqtt.password` without `mqtt.host` reads without error. A root that is not a mapping raises `ConfigError`. A YAML mistake raises `ConfigError` that names the file, line and column. For `password: [pw-8c41f2` and `password: *pw-8c41f2`, the message does not contain `pw-8c41f2`, and holds no PyYAML text. Verify they fail.
- [x] 1.2 Add `read_config_mapping` to `pierpressure/core/config.py`, and make `read_config` build its `ConfigFile` from it. Update both docstrings. Verify the 1.1 tests pass, the existing `read_config` and `load_config` tests pass without other changes, and `tests/test_core_boundary.py` still passes.

## 2. One "set" rule for the form

- [x] 2.1 Write failing tests in `tests/test_addon_options.py` (design D2):
  - `min_altitude` saved as empty or blank text counts as unset, so the pier gets no `horizon` block.
  - Each equipment field saved as empty or blank text counts as unset.
  - `min_altitude` of 0 still counts as set.
  - A new function names the settings a raw form pier sets: `horizon` for `min_altitude` or `horizon_points`, `equipment` for any equipment field or an `equipment` value, no setting for `id`, and the key itself for anything else. Unset values name nothing.
  - Every pier field in the `schema` of `ha-addon/config.yaml` is either a known horizon or equipment field, `id`, or maps to itself.

  Verify they fail.
- [ ] 2.2 In `pierpressure/addon_options.py`, add one shared "is set" function, and use it for the horizon and equipment fields. Add the function that names a raw pier's settings, beside `EQUIPMENT_FIELDS`. Update the module and function docstrings. Verify the 2.1 tests and the existing tests in the file pass.

## 3. Combining the form and the file

- [ ] 3.1 Write failing tests in a new `tests/test_addon_settings.py` for the combine step, one per scenario of the requirement "The add-on combines the Configuration form with config.yaml" that does not need the service (design D1 to D3, D5):
  - The file adds a horizon file, `go_threshold`, `max_gust`, `explainer` and `mqtt.base_topic`, and file horizon points when the form sets none.
  - A file pier with only an `id` adds nothing.
  - Each conflict stops with an error that names the setting and the pier: horizon, horizon with a floor of 0, equipment, a plain pier key such as `latitude`, the broker connection, and the recompute interval.
  - A file pier the form does not list, a pier listed twice in the file, a file pier that is not a mapping, and a file pier whose `id` is missing, null, a number, a list or a mapping. The last two name the entry's position.
  - A file `piers` that is not a list.
  - A file entry for a form pier the translation skips raises no error, and is dropped.
  - Several problems give one error that names each of them, on one line.
  - An `id` with a line break is shown escaped.
  - With `pw-8c41f2` as the password in both sources, no error contains it.
  - The form's pier order is kept. When the form lists an id twice, the file entry applies to both.

  Verify they fail.
- [ ] 3.2 Create `pierpressure/addon_settings.py` with the combine step. It takes the raw form values and the file's mapping. It returns one config-shaped mapping, or raises one `ConfigError` that lists every problem. Verify the 3.1 tests pass, and `just check` is green.

## 4. One place to set the broker in Supervisor errors

- [ ] 4.1 Change the tests in `tests/test_supervisor.py` (design D7). The "no MQTT broker was found", "access refused", TLS and MQTT version errors each say to set `mqtt.host` "on the Configuration tab or in config.yaml". Remove the tests for a caller-supplied place. Verify they fail.
- [ ] 4.2 In `pierpressure/supervisor.py`, replace `CONFIG_FILE_PLACE` with one constant for that phrase, and remove the `settings_place` parameter. Verify the 4.1 tests pass.

## 5. Startup reads both sources

- [ ] 5.1 Write failing tests in `tests/test_main.py` for `load_app_config`, inside an add-on with a temporary `options.json` and `config.yaml` (design D4, D6 to D8):
  - "Form setup gives a verdict without a file": settings from the form only, and the log says `Settings from the Configuration tab`.
  - "A form pier takes its horizon file from config.yaml": a relative `.hrz` path is read from the config folder, and the log says `Settings from the Configuration tab and config.yaml`.
  - "The file's broker wins", "The file sets only its topics" and "Credentials without a host are rejected", with a form that sets no broker field.
  - A form host with a file `mqtt.password` reports the broker connection as set in both, not "set without mqtt.host".
  - The broker log line names the Configuration tab, `config.yaml` or the Supervisor, by where the host came from.
  - "Nothing is set up", with and without a file. "An empty form names the file's piers" names `roof` and `shed`. An empty form with a broken file still gives the short "Nothing is set up" error.
  - "A config.yaml that is not valid YAML stops the add-on" names `/config/config.yaml`.
  - Supervisor errors and the Supervisor login advice say "on the Configuration tab or in config.yaml", and never say that `config.yaml` is not read.
  - Outside an add-on, `config.yaml` loads on its own as before.

  Replace the tests that expect the "config.yaml is ignored" warning, the empty-form fallback, or `FORM_NOTE`. Verify the new tests fail.
- [ ] 5.2 Change `load_app_config` in `pierpressure/__main__.py` to read the form and the file and combine them. Raise the "Nothing is set up" error for an empty form, naming the file's piers when it can. Remove `FORM_PLACE`, `FORM_NOTE`, `FORM_LOGIN_ADVICE`, `LoadedConfig.from_form` and the `from_form` parameter of `build_delivery_and_explainer`. Reword `SUPERVISOR_LOGIN_ADVICE`. Update the module and function docstrings. Verify the 5.1 tests and the rest of `tests/test_main.py` pass.
- [ ] 5.3 Update the comments in `ha-addon/config.yaml` that say `config.yaml` is read only while the form lists no piers. Verify `tests/test_ha_addon.py` passes.
- [ ] 5.4 Run `just check` and verify that it is green.

## 6. Documentation

- [ ] 6.1 Update `ha-addon/DOCS.md` (design D9):
  - Replace "The form or the file" with a section on how they combine. Cover which settings each source owns, the four groups, the conflict rule, and a horizon file example.
  - Remove "Set up with config.yaml instead".
  - Point "More settings" to `config.yaml` for settings the form leaves unset.
  - Add rows to the troubleshooting table for a conflict, a file pier not on the form, and an empty form. Update the rows that name `config.yaml`.

  Verify by reading the rendered Markdown, and check that no sentence says `config.yaml` is ignored or read only while the form is empty.
- [ ] 6.2 Update the add-on section of `README.md` to match 6.1. Verify that it no longer tells add-on users to set up with `config.yaml` alone.
- [ ] 6.3 Run `just check` and verify that it is green.
