## Context

See proposal.md for why, and the two delta specs for the required behaviour. This
design covers how the core keeps a secret out of an error about the `mqtt` or
`explainer` block, and out of a printed setting.

Facts that shape the approach:

- **Pydantic puts the input into its errors.** The text of a `ValidationError`
  shows each failing value as `input_value=...`. `build_config` in
  `pierpressure/core/config.py` copies that text into the `ConfigError` that
  `__main__` logs.
- **`hide_input_in_errors` hides values, not key names.** For a key the model
  does not define, the error's location is the key's name. We tested this on
  Pydantic 2.13.5: with the setting on, an unknown key named `hunter2` still
  appears in the error text.
- **`hide_input_in_errors` works only on the model being validated.** When a
  model is validated as a field of a parent model, the parent's setting applies,
  and the value shows.
- **`build_config` validates the two blocks differently.** It validates `mqtt`
  directly with `MqttConfig.model_validate`. It validates `explainer` only as a
  field of `AppConfig`, in the last `AppConfig.model_validate` call.
- **An empty `explainer` block loads today.** `explainer:` with no value reaches
  `AppConfig` as `None`, which means "disabled".
- **`ConfigFile` already checks that `mqtt` is a mapping.** Its
  `__post_init__` raises a `ConfigError` with no value in it. It does not check
  `explainer`.
- **Three objects print secrets in plain text today.** `MqttConfig` and
  `ExplainerConfig` hold them as `str`. `ConfigFile.raw` and `BrokerSettings` are
  dataclasses whose default `repr` prints every field.
- **The add-on's broker conflict error names keys.** `_check_broker` in
  `pierpressure/addon_settings.py` names each `mqtt` key that both the form and
  the file set, whether or not the core defines it.

## Goals / Non-Goals

**Goals:**

- No error about the `mqtt` or `explainer` block holds text from that block,
  other than the names of the settings the core defines.
- No printed or logged settings object shows either secret.
- The core does this, so every interface gets it.

**Non-Goals:**

- Hiding the values in pier errors. A pier error keeps its values so the user can
  fix them.
- Scanning log output for secrets, or redacting text after the fact.

## Decisions

### D1: Write the block errors from the error's parts, not its text

For the `mqtt` and `explainer` blocks, `build_config` does not copy the
`ValidationError` text. It builds the message from
`exc.errors(include_input=False)`, one problem per error:

- When the location is a field the model defines, the problem is the dotted
  setting name, such as `mqtt.port`, and Pydantic's `msg`. The `msg` states the
  rule, such as "Input should be a valid integer", and holds no input.
- When the location is a key the model does not define, the problem is "the mqtt
  block holds a setting it does not know". The message then lists the model's
  defined fields once.

`MqttConfig` and `ExplainerConfig` also set `hide_input_in_errors=True`. This is
a second guard: code that prints the `ValidationError` itself still shows no
value.

*Alternative:* rely on `hide_input_in_errors` alone. Rejected: it leaves an
unknown key's name in the text.

*Alternative:* name an unknown key only when it looks like a typo of a defined
field. Rejected: a rule that guesses what is safe to show is harder to test, and
"list the defined settings" gives the user the same help.

### D2: Validate `explainer` directly, as `mqtt` already is

When the `explainer` block is present and not `None`, `build_config` calls
`ExplainerConfig.model_validate` on it before it assembles `AppConfig`. It
formats any error as D1 describes. It then passes the validated model into
`AppConfig`. Pydantic does not validate a model instance again by default, so the
last `AppConfig.model_validate` call never sees the raw block. A `None` block
passes through as today, and still means "disabled".

*Alternative:* set `hide_input_in_errors=True` on `AppConfig`. Rejected: the last
`AppConfig.model_validate` call runs each pier's validator again, so it would also
hide pier values, which the user needs. It would also leave key names in the
text.

### D3: `ConfigFile` checks that `explainer` is a mapping

`ConfigFile.__post_init__` already rejects an `mqtt` value that is not a mapping.
It rejects an `explainer` value that is neither a mapping nor `None` in the same
way: "The explainer block must be a mapping of settings, such as
explainer.enabled". The error holds no value. Both blocks then follow one rule in
one place.

### D4: Mask valid secrets wherever they are held

`MqttConfig.password` and `ExplainerConfig.api_key` become `SecretStr | None`.
`SecretStr` prints as `**********` in `repr`, `str` and model dumps.

The code reads the value with `get_secret_value()` only at the two places that
need it:

- The MQTT client calls `username_pw_set` in `pierpressure/delivery/mqtt.py`.
- `PydanticAIProvider` sets the provider's key variable in
  `_provider_key_env` in `pierpressure/explain/provider.py`. The provider holds
  the key as `SecretStr` too, so its dataclass `repr` masks it. `_key_is_usable`
  reads the value to check that it is set and fully expanded.

The two dataclasses that hold settings before validation get
`field(repr=False)`:

- `ConfigFile.raw`, which holds the whole read mapping, both secrets included.
- `BrokerSettings.password`, the broker password from the Supervisor.

*Alternative:* leave the valid secrets as `str`, and rely only on D1 to D3.
Rejected: the story asks for both. Any later log line that prints the settings
would leak a secret again.

### D5: The add-on's broker conflict names only defined settings

`_check_broker` reports a non-connection key that both the form and the file set
only when `MqttConfig` defines it. A key the core does not define is not reported
as a conflict there. The core then rejects it as D1 describes, without its name.

### D6: Test with a marker secret on every path

Each planned test puts a unique marker into the secret, or into an unknown key's
name, and makes the configuration fail in one way. It then checks that the marker
is in neither the `ConfigError` message nor any `caplog` record. The paths are:

- the secret is a number (`mqtt.password`, `explainer.api_key`)
- an unknown key beside the secret, as `key: marker` and as a bare `marker:` key
- the block is a list holding the marker
- the add-on's combined form-and-file path, through `load_app_config`, with a
  failing `mqtt` block and with a broker conflict
- `main()`, end to end, so the `Configuration error` log line is checked too
- `repr` of `ConfigFile`, `BrokerSettings`, `AppConfig` and `PydanticAIProvider`
  for a valid configuration

Each failure test also checks that the error still names the setting, or lists
the defined settings. A test then cannot pass because the error is empty.

## Risks / Trade-offs

- [The error no longer names a misspelled key, such as `pasword`.] → The error
  lists the defined settings, so the user can compare them with their file.
- [`hide_input_in_errors` hides non-secret values in the two blocks, such as a
  bad `port`.] → The error still names the field and the rule it broke. A user
  can see their own `port` in `config.yaml`.
- [Existing tests compare the secrets to plain text or pass them as `str`.] →
  Those tests read the value with `get_secret_value()`, or build a `SecretStr`.
  The test files are `tests/test_config.py`, `tests/test_explainer_config.py`,
  `tests/test_explainer_docs.py`, `tests/test_explainer.py` and
  `tests/test_main.py`.
- [A later Pydantic release could change how errors hold input.] → The D6 tests
  go through `build_config` and `main()`, so they fail if a secret shows again.
- [A user types a secret into a pier field.] → The pier's error shows it. The
  specs scope this requirement to the `mqtt` and `explainer` blocks on purpose.

## Migration Plan

None for users. Every configuration that loads today loads the same way,
including an empty `explainer` block. A configuration that fails today still
fails. Errors about the `mqtt` and `explainer` blocks change their wording: they
show no values and no unknown key names, and they list the defined settings
instead.
