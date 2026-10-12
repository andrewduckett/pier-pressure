## 1. One connection rule for every source of settings

- [x] 1.1 Write failing tests in `tests/test_config.py` (design D3). Building a `ConfigFile` directly, with an `mqtt` block that sets `port`, `username` or `password` but no `host`, raises `ConfigError` with the same message `read_config` gives today (parameterized over the three keys). A `ConfigFile` whose `mqtt` is not a mapping raises the same error as today. Verify they fail.
- [x] 1.2 Move both checks from `read_config` into `ConfigFile.__post_init__` in `pierpressure/core/config.py`, and update the docstrings of both. Verify the 1.1 tests pass, and that the existing `read_config` tests pass without changes.

## 2. The add-on manifest and its labels

- [x] 2.1 Write failing tests in `tests/test_ha_addon.py` (design D1). `options` sets `mqtt` to an empty mapping. `schema` declares `mqtt` as a mapping of `host: str?`, `port: port?`, `username: str?` and `password: password?`. Verify they fail.
- [x] 2.2 Add the `mqtt` block to `options` and `schema` in `ha-addon/config.yaml`, with a comment naming this change's D1. Add names and descriptions for `mqtt` and its four fields in `ha-addon/translations/en.yaml`. The `port` description says the default is 1883. Verify the 2.1 tests pass, and extend the label test so it covers the `mqtt` fields.

## 3. The form's broker reaches the settings

- [x] 3.1 Write failing tests in `tests/test_addon_options.py` for `read_addon_options` (design D2):
  - A form with piers and a full `mqtt` block gives the same `mqtt` block in the result.
  - Fields that are `null`, empty text or blank text are left out of the block.
  - An empty `mqtt` block, or one whose fields are all left out, gives no `mqtt` key.
  - A form with no piers still returns `None`, whatever its `mqtt` block holds.

  Verify they fail.
- [x] 3.2 Change `pierpressure/addon_options.py` to copy the form's `mqtt` block, without empty fields, and update its module and function docstrings. Verify the 3.1 tests and the existing tests in the file pass.

## 4. Advice and log lines that name the right source

- [x] 4.1 Write failing tests in `tests/test_supervisor.py` for `fetch_mqtt_broker` (design D5). By default, the "no MQTT broker was found", "access refused", TLS and MQTT version errors still name `config.yaml`. Given the Configuration tab as the place, each error names it and does not name `config.yaml`. Verify they fail.
- [x] 4.2 Add the keyword argument to `fetch_mqtt_broker` in `pierpressure/supervisor.py`, and use it in each error. Verify the 4.1 tests and the existing tests in the file pass.
- [x] 4.3 Write failing tests in `tests/test_main.py` for `load_app_config` and `build_delivery_and_explainer`, inside an add-on with a temporary `options.json` (design D4 to D6):
  - Each scenario in the requirement "The form sets the broker": the form's broker is used and the Supervisor is not asked; port 1883 by default; blank fields count as not set; a username without a host stops the add-on before the Supervisor is asked; a rejected login gives the adapter's default advice, with no mention of Mosquitto.
  - The log names the Configuration tab, `broker.lan` and the port, and contains no `pw-8c41f2`, at startup and after a rejected login.
  - "An empty form's broker is not used": the Supervisor's broker is used.
  - On the form path without a host, a Supervisor error says `config.yaml` is not read, names the Configuration tab, and does not name `config.yaml` as the place to set `mqtt.host`. Cover the "no broker found" and TLS errors.
  - The login advice for a Supervisor broker on the form path names the Configuration tab and not moving piers into `config.yaml`.
  - The file path's log line and advice do not change.

  Verify they fail.
- [x] 4.4 Change `pierpressure/__main__.py`: shorten `FORM_NOTE`, reword `FORM_LOGIN_ADVICE`, pick the login advice by the broker's source, pass the place to `fetch_mqtt_broker`, and name the Configuration tab in the broker log line. Update the module and function docstrings. Verify the 4.3 tests and the existing tests in the file pass.
- [x] 4.5 Run `just check` and verify that it is green.

## 5. Documentation

- [ ] 5.1 Update `ha-addon/DOCS.md`. Describe the four broker fields, and say they apply only while the form lists piers. Say that a host makes the add-on take all four settings from the form, and that leaving it empty uses the Mosquitto add-on. Say that the password field hides its value on the form, and that the Supervisor stores it, not `config.yaml`; do not say it is encrypted. Remove the advice to write the password into `config.yaml`. Update the troubleshooting table so a form user is told to set `mqtt.host` on the Configuration tab. Verify by reading the rendered Markdown.
- [ ] 5.2 Update the README's add-on section in `README.md` to match 5.1. Verify that it no longer advises writing the broker password into `config.yaml` in the add-on.

## 6. Live check

- [ ] 6.1 The maintainer checks the form on a real Home Assistant OS instance, with an add-on built from this branch, as in addon-options-form task 6.1. Record the Home Assistant and Supervisor versions in the PR, with the result of each of the four pass conditions in the design's risks section. If no instance is available before merge, record that the check is still open.
