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

- **An error about the `mqtt` or `explainer` block shows none of the block's
  text.** It shows no value, and it does not name a key the block does not
  define, because a user can type a secret where a key name belongs. This
  protects the broker's `password` and the explainer's `api_key` against:
  - a password or API key made only of digits
  - a misspelled key beside the secret, such as `pasword`
  - an `mqtt` or `explainer` block that is not a mapping
- **The error still says what is wrong.** It names a defined setting, such as
  `mqtt.password`, and states the rule it broke. For a key the block does not
  define, it says so and lists the settings the block defines.
- **A valid secret stays masked.** The core holds both secrets in a type that
  prints as a mask. The code reads the value only where it builds the
  explainer's provider or logs in to the broker.
- **The rule lives in the core,** so it holds the same for every interface: the
  add-on's form, `config.yaml`, and Docker and source installs.

Out of scope:

- Errors about piers. They keep showing their values, so a user can find and fix
  a bad latitude or horizon. A user who types a secret into a pier field will
  see it in that pier's error.
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
  - `pierpressure/core/config.py`: `MqttConfig`, `ExplainerConfig`,
    `ConfigFile`, `BrokerSettings` and `build_config`.
  - `pierpressure/addon_settings.py`: the broker conflict error names only
    defined `mqtt` settings.
  - `pierpressure/explain/explainer.py` and `pierpressure/explain/provider.py`:
    read the API key's value where the provider is built.
  - `pierpressure/delivery/mqtt.py`: read the password's value where the MQTT
    client logs in.
- **Tests:** a marker secret passes through each way a configuration can fail.
  The tests check that the marker is in no error message and no log line,
  including on the add-on's combined form-and-file path.
- **Unchanged:** the `config.yaml` format, the add-on's form, and every
  configuration that loads today, including an empty `explainer` block.
- **Changed error text:** errors about the `mqtt` and `explainer` blocks no
  longer show values or unknown key names, and list the defined settings
  instead.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
