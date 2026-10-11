## 1. The add-on manifest and its labels

- [x] 1.1 Write failing tests in `tests/test_ha_addon.py`. Replace `test_addon_offers_no_options` with tests that check the manifest's `options` (`interval_seconds: 900`, `piers: []`) and `schema` (design D5). Add a test that every key in `schema`, and every pier field, has a `name` and a `description` in `ha-addon/translations/en.yaml` (design D6). Verify both fail.
- [x] 1.2 Add `options` and `schema` to `ha-addon/config.yaml`, and update its comment that says there is no options form. Create `ha-addon/translations/en.yaml`, with units in each number's description. Verify the 1.1 tests pass.

## 2. Reading the form

- [x] 2.1 Write failing tests in a new `tests/test_addon_options.py` for the function in `pierpressure/addon_options.py` (design D1, D3). Cover these cases: a form with piers returns the config-shaped mapping; a form with no piers returns `None`; a missing file returns `None`; invalid JSON, a non-mapping root, and a non-list `piers` each raise `ConfigError` naming the file. Verify they fail.
- [x] 2.2 Implement `pierpressure/addon_options.py` outside the core. Add `pierpressure.addon_options` to the forbidden imports in `tests/test_core_boundary.py`. Verify the 2.1 tests and the boundary test pass.

## 3. Choosing the source at startup

- [x] 3.1 Write failing tests in `tests/test_main.py` for `load_app_config` and `main` (design D2, D4). Use a temporary `options.json` and the existing `StartupStub`. Cover each scenario in the requirement "The add-on reads the Configuration form before the config file":
  - a form setup with no file publishes the form's pier, using the Supervisor's broker and the form's interval
  - an empty form falls back to the file
  - the form wins over an existing file, with a warning naming the file
  - a pier with latitude 95 in the saved values is skipped, and the other pier is kept
  - with nothing set up, the error names the file and the Configuration tab
  - outside an add-on, the form is never read

  Verify they fail.
- [x] 3.2 Change `load_app_config` in `pierpressure/__main__.py`: read the form first inside an add-on, and log the settings' source. Take the `options.json` path as an argument that defaults to `/data/options.json`. Verify the 3.1 tests pass, and the existing add-on and broker tests pass unchanged.

## 4. Broker errors for form users

- [x] 4.1 Write failing tests: on the form path, a "no MQTT broker was found" `SupervisorError`, and a rejected login, each say that `config.yaml` is not read while the form lists piers. On the file path, both keep today's wording. Verify they fail.
- [x] 4.2 On the form path, add the note to `SupervisorError` in `load_app_config`. Have `load_app_config` report that the form was the source, and pass that through `main` to `build_delivery_and_explainer`, which picks login advice for form users (design, "Risks / Trade-offs"). Verify the 4.1 tests pass and `just check` is green.

## 5. Documentation

- [ ] 5.1 Rewrite "Set up the add-on" in `ha-addon/DOCS.md`: the Configuration tab is the main path, and `config.yaml` is the alternative for settings the form lacks. Explain the "form or file" rule and the warning. Add the new missing-setup error to the startup-error table. Verify by reading the rendered Markdown.
- [ ] 5.2 Update the README's add-on section (`README.md`, "Install as a Home Assistant add-on") to match 5.1, without asking for a second add-on. Verify that the README's add-on steps name the Configuration tab.

## 6. Live check

- [ ] 6.1 The maintainer checks the form on a real Home Assistant OS instance. The add-on pulls only released images, so copy `ha-addon/` into the instance's local `/addons` folder, and point its `image` at an image built from this branch. Add one pier on the Configuration tab, with no `config.yaml`, and start the add-on. Check that the form shows the list of piers with labels, not YAML mode, and that a verdict device appears. Record the Home Assistant and Supervisor versions and the result in the PR. If no instance is available before merge, record that the check is still open.

## Archive note

When archiving, edit the Purpose of `openspec/specs/ha-addon/spec.md` directly in the archive commit. It says the add-on's "only behaviour of its own" is using the Supervisor's broker; it now also reads the Configuration form.
