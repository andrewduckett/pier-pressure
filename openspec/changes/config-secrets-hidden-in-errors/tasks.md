## 1. Errors about the mqtt block

- [x] 1.1 Write failing tests in `tests/test_config.py` for `build_config` (design D1, D6). Use a marker secret in each case, and check that the marker is in neither the `ConfigError` message nor any `caplog` record, and not in `traceback.format_exception` of the error:
  - `mqtt.password` is a number; the error names `mqtt.password`
  - the `mqtt` block holds `pasword: <marker>`, and, as a separate case, a bare `<marker>:` key; the error says the block holds a setting it does not know, and lists the defined `mqtt` settings
  - `mqtt` is a list that holds the marker; the error says `mqtt` must be a mapping of settings
  - a bad `recompute.interval_seconds` still shows its current error text

  Verify the number, unknown key and traceback cases fail.
- [x] 1.2 In `pierpressure/core/config.py`, set `hide_input_in_errors=True` on `MqttConfig`, with a comment that its checks must not quote their input. Validate `mqtt` and `recompute` in separate steps. Build the `mqtt` error from `exc.errors(include_input=False)`, as design D1 describes, and raise it `from None`. Verify the 1.1 tests and the existing tests in `tests/test_config.py` pass.

## 2. Errors about the explainer block

- [x] 2.1 Write failing tests in `tests/test_explainer_config.py` (design D1-D3, D6), with the same marker checks as 1.1:
  - `explainer.api_key` is a number; the error names `explainer.api_key`
  - the block holds `apikey: <marker>`, and, as a separate case, a bare `<marker>:` key; the error says the block holds a setting it does not know, and lists the defined `explainer` settings
  - `explainer` is a list, and, as a separate case, text, holding the marker; the error says `explainer` must be a mapping of settings
  - `explainer:` with no value, and `explainer: {}`, each load with the explainer disabled

  Verify the number, unknown key, list and traceback cases fail.
- [x] 2.2 In `pierpressure/core/config.py`, set `hide_input_in_errors=True` on `ExplainerConfig`, with the same comment as 1.2. Make `ConfigFile.__post_init__` reject an `explainer` value that is neither a mapping nor `None`, worded like its `mqtt` check. In `build_config`, validate a present, non-`None` `explainer` block directly with `ExplainerConfig.model_validate`, format its error as in 1.2, and pass the validated model into `AppConfig`. Reuse one formatter for both blocks. Verify the 2.1 tests and the existing explainer tests pass.

## 3. Masking valid secrets

- [x] 3.1 Write failing tests (design D4, D6). For a valid configuration with a marker password and a marker API key, check that the marker is not in the `repr` of `ConfigFile`, `AppConfig`, `BrokerSettings` and `PydanticAIProvider`, nor in `AppConfig.model_dump()`. Add the same check for `CombinedSettings` in `tests/test_addon_settings.py`. Verify they fail.
- [x] 3.2 Make `MqttConfig.password` and `ExplainerConfig.api_key` `SecretStr | None`. Give `ConfigFile.raw`, `CombinedSettings.raw` and `BrokerSettings.password` `field(repr=False)`. Verify the 3.1 tests pass.
- [x] 3.3 Read the password with `get_secret_value()` where `pierpressure/delivery/mqtt.py` calls `username_pw_set`. Verify a test with a stub client in `tests/test_publish.py` or `tests/test_main.py` still receives the plain password.
- [x] 3.4 Make `PydanticAIProvider.api_key` a `SecretStr | None`, and pass it from `build_explainer` unchanged. Read its value only in `_key_is_usable` and `_provider_key_env`. Verify the tests in `tests/test_explainer.py` pass, including the ones that check the key variable is set only during the call and that an unexpanded `${VAR}` counts as no key.
- [x] 3.5 Update the existing tests that compare a secret to plain text, in `tests/test_config.py`, `tests/test_explainer_config.py`, `tests/test_explainer_docs.py`, `tests/test_explainer.py` and `tests/test_main.py`, to read the value with `get_secret_value()` or build a `SecretStr`. Verify that `uv run mypy` reports no errors.

## 4. The add-on's combined settings

- [ ] 4.1 Write failing tests in `tests/test_addon_settings.py` (design D5). The form and the file's `mqtt` blocks both set a key the core does not define, with a marker as its name and value; check that `combine_settings` does not report it as a conflict, and that the marker is not in any error. Verify it fails.
- [ ] 4.2 Change `_check_broker` in `pierpressure/addon_settings.py` to report a non-connection key in both sources only when `MqttConfig` defines it. Verify the 4.1 test and the existing conflict tests pass.
- [ ] 4.3 Write tests in `tests/test_main.py` for `load_app_config` inside an add-on, covering the `ha-delivery` scenarios for the combined path, with a marker password set on the form:
  - the file's `mqtt` block holds `pasword: <marker>`; the add-on stops with an error that says the block holds a setting it does not know
  - the form and the file both set the broker host; the add-on stops with a conflict error

  Check that the marker is in neither the error nor any `caplog` record. Verify they pass.

## 5. End to end

- [ ] 5.1 Write a parameterized test in `tests/test_main.py` that runs `main()` with a `config.yaml` that fails in one way per case: `mqtt.password` is a marker number, or the `explainer` block holds an unknown key named after a marker. Check that `main()` returns 1, that the `Configuration error` log line names the block, and that no `caplog` record holds the marker. Verify it passes.
- [ ] 5.2 Run `just check` and verify that it is green.
