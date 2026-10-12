## ADDED Requirements

### Requirement: An error about the explainer settings shows none of their text

When the process rejects the `explainer` block, the error and the log SHALL NOT
contain any value from that block. They SHALL NOT contain the name of a key that
the block does not define either, because a user can type a secret where a key
name belongs. This SHALL hold for every source of settings.

The error SHALL still say what is wrong:

- For a defined setting, it SHALL name the setting, such as `explainer.api_key`,
  and state the rule the value broke.
- For a key the block does not define, it SHALL say that the block holds a
  setting it does not know, and list the settings the block defines.
- For an `explainer` value that is not a mapping or empty, it SHALL say that
  `explainer` must be a mapping of settings.

An empty `explainer` block SHALL still mean that the explainer is disabled.

Once the configuration is valid, the process SHALL show the API key as a mask
whenever it prints or logs its settings. It SHALL use the key's value only to
call the LLM provider.

#### Scenario: An API key that is not text is rejected without its value

- **WHEN** `config.yaml` sets `explainer.api_key` to a number, such as `12345`
- **THEN** the process stops with a configuration error that names
  `explainer.api_key`
- **AND** neither the error nor the log contains `12345`

#### Scenario: An unknown key in the explainer block is not named

- **WHEN** the `explainer` block in `config.yaml` holds a key it does not define,
  such as `apikey: sk-secret`, or a bare key `sk-secret`
- **THEN** the process stops with a configuration error that says the
  `explainer` block holds a setting it does not know
- **AND** the error lists the settings the `explainer` block defines
- **AND** neither the error nor the log contains `apikey` or `sk-secret`

#### Scenario: An explainer block that is not a mapping does not show its value

- **WHEN** `config.yaml` sets `explainer` to a list or text that holds a secret
- **THEN** the process stops with a configuration error that says `explainer`
  must be a mapping of settings
- **AND** neither the error nor the log contains the secret

#### Scenario: An empty explainer block still disables the explainer

- **WHEN** `config.yaml` has an `explainer` key with no value
- **THEN** the configuration loads
- **AND** no narrative is produced

#### Scenario: A valid API key is masked when the settings are printed

- **WHEN** the configuration is valid and sets an explainer API key
- **AND** the process prints or logs its settings, at any stage of loading them
- **THEN** the output does not contain the API key
