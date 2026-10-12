## Context

See proposal.md for why, and the two delta specs for the required behaviour. This
design covers where the core hides each secret, and why one setting alone is not
enough.

Facts that shape the approach:

- **Pydantic puts the input into its errors.** A `ValidationError` shows each
  failing value as `input_value=...`. `build_config` in
  `pierpressure/core/config.py` copies the whole error into the `ConfigError`
  that `__main__` logs.
- **`hide_input_in_errors` works only on the model being validated.** We tested
  this on Pydantic 2.13.5. Set on a model, it hides values when that model is
  validated directly. When the same model is validated as a field of a parent
  model, the parent's setting applies, and the value shows.
- **`build_config` validates the two blocks differently.** It validates `mqtt`
  directly with `MqttConfig.model_validate`. It validates `explainer` only as a
  field of `AppConfig`, in the last `AppConfig.model_validate` call.
- **`ConfigFile` already checks that `mqtt` is a mapping.** Its
  `__post_init__` raises a `ConfigError` with no value in it. It does not check
  `explainer`.
- **A secret has three ways into an error.** These are a value of the wrong type
  (a YAML number), an unknown key beside it (`extra="forbid"` shows the key's
  value), and a block that is not a mapping.
- **The secrets are plain `str` once valid.** `MqttConfig.password` and
  `ExplainerConfig.api_key` print their values in any `repr` or model dump.
  `BrokerSettings` is a dataclass, so its default `repr` prints the
  Supervisor's broker password.

## Goals / Non-Goals

**Goals:**

- No configuration error and no log line holds the broker password or the
  explainer's API key, for any input.
- The core does this, so every interface gets it.

**Non-Goals:**

- Hiding the values in pier errors. A pier error keeps its values so the user can
  fix them.
- Scanning log output for secrets, or redacting text after the fact.

## Decisions

### D1: Hide the input on the two models that hold a secret

`MqttConfig` and `ExplainerConfig` set `hide_input_in_errors=True`. This covers
both a wrong type and an unknown key, because Pydantic hides every input in that
model's errors.

The setting also hides the values of the other fields in these two blocks, such
as a bad `port` or `model`. The error still names the field and the problem. We
accept this, because a user can see their own `port` in `config.yaml`.

*Alternative:* hide only the secret field, with a custom validator that raises
its own message. Rejected: it does not cover an unknown key beside the secret,
because that error belongs to the model, not to the field.

### D2: Validate `explainer` directly, as `mqtt` already is

`build_config` calls `ExplainerConfig.model_validate` on the `explainer` block
before it assembles `AppConfig`. It then passes the validated model into
`AppConfig`. Pydantic does not validate a model instance again by default, so the
last `AppConfig.model_validate` call cannot show the key.

An error from this step becomes a `ConfigError` labelled for the explainer, in
the same way as the existing `mqtt` and `recompute` label.

*Alternative:* set `hide_input_in_errors=True` on `AppConfig`. Rejected: the last
`AppConfig.model_validate` call runs each pier's validator again, so it would also
hide pier values, which the user needs.

### D3: `ConfigFile` checks that `explainer` is a mapping

`ConfigFile.__post_init__` already rejects an `mqtt` value that is not a mapping.
It does the same for `explainer`, with the same wording: "The explainer block
must be a mapping of settings, such as explainer.enabled". The error holds no
value.

D1 alone would already hide the value here. The explicit check gives a clearer
message, and it puts both blocks under one rule in one place.

### D4: Keep valid secrets in `SecretStr`

`MqttConfig.password` and `ExplainerConfig.api_key` become `SecretStr | None`.
`SecretStr` prints as `**********` in `repr`, `str` and model dumps.

The code reads the value with `get_secret_value()` only at the two places that
need it:

- The MQTT client calls `username_pw_set` in `pierpressure/delivery/mqtt.py`.
- `PydanticAIProvider` sets the provider's key variable in
  `_provider_key_env` in `pierpressure/explain/provider.py`. The provider holds
  the key as `SecretStr` too, so its dataclass `repr` hides the key.
  `_key_is_usable` reads the value to check it is set and fully expanded.

`BrokerSettings.password` stays a `str`, because `build_config` passes it into
`MqttConfig`, which wraps it. The field gets `repr=False`, so a printed
`BrokerSettings` no longer shows it.

*Alternative:* leave the valid secrets as `str`, and rely only on D1 and D2.
Rejected: the story asks for both. Any later log line that prints the settings
would leak the secret again.

### D5: Test with a marker secret on every path

Each test puts a unique marker string, or a marker number, into the secret, and
makes the configuration fail in one way. It then checks that the marker appears
neither in the `ConfigError` message nor in any `caplog` record. The paths are:

- the secret is a number (`mqtt.password`, `explainer.api_key`)
- an unknown key beside the secret holds the marker
- the block is a list holding the marker
- the add-on's combined form-and-file path, through `load_app_config`
- `main()`, end to end, so the `Configuration error` log line is checked too

Each test also checks that the error still names the setting, so a test cannot
pass because the error is empty.

## Risks / Trade-offs

- [Existing tests compare the secrets to plain text.] → Those tests read the
  value with `get_secret_value()`. The test files are `tests/test_config.py`,
  `tests/test_explainer_config.py`, `tests/test_explainer_docs.py` and
  `tests/test_main.py`.
- [D1 hides non-secret values in the `mqtt` and `explainer` blocks.] → The error
  still names the field and the rule it broke. These blocks are short.
- [A later Pydantic release could change how nested models hide input.] → The D5
  tests go through `build_config`, so they fail if a secret shows again.
- [Unexpanded `${VAR}` placeholders.] → No change. `_key_is_usable` reads the
  value and still treats a placeholder as no key.

## Migration Plan

None. Every configuration that loads today loads the same way. A configuration
that fails today fails with the same error, with the secret's value left out.
