## Why

A configuration error can print the explainer's API key or the broker password.
The error ends up in the log, and a user may paste that log into a bug report or a
support post.

The leak happens because Pydantic puts the bad input into its error message, and
`build_config` copies that message into the `ConfigError` it logs. A typo is
enough to cause it. For example, a password made only of digits is read from YAML
as a number, and the error that rejects it shows the number.

Story: #89 `config-secrets-hidden-in-errors`.

## What Changes

- **A configuration error never shows a secret.** This covers the explainer's
  `api_key` and the broker's `password`, whatever the user typed. Examples:
  - a password or API key made only of digits
  - a misspelled key beside the secret, such as `pasword`
  - an `mqtt` or `explainer` block that is not a mapping
- **The error still says what is wrong.** It names the setting, such as
  `mqtt.password`, and the problem, but not the value.
- **A validated secret stays hidden.** The core holds both secrets in a type that
  hides its value when it is printed or logged. The code reads the value only
  where it builds the explainer's provider or the MQTT client.
- **The rule lives in the core,** so it holds the same for every interface: the
  add-on's form, `config.yaml`, and Docker and source installs.

Out of scope:

- Errors about piers. They keep showing their values, so a user can find and fix
  a bad latitude or horizon.
- How secrets are supplied, such as `${ENV}` in `config.yaml` or the form's
  `password` field.
- Moving the add-on's own checks into the core. Story #83 does that.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: a configuration error never shows the broker password.
- `verdict-narrative`: a configuration error never shows the explainer's API key.

## Impact

- **Changed files:**
  - `pierpressure/core/config.py`: `MqttConfig`, `ExplainerConfig` and
    `build_config`.
  - `pierpressure/explain/explainer.py` and `pierpressure/explain/provider.py`:
    read the API key's value where the provider is built.
  - `pierpressure/delivery/mqtt.py`: read the password's value where the MQTT
    client logs in.
- **Tests:** a marker secret passes through each way a configuration can fail.
  The tests check that the marker is in no error message and no log line,
  including on the add-on's combined form-and-file path.
- **Unchanged:** the `config.yaml` format, the add-on's form, and every
  configuration that loads today.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
