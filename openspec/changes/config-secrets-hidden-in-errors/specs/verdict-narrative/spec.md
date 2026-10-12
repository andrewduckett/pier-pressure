## ADDED Requirements

### Requirement: A configuration error never shows the explainer's API key

When the process rejects its configuration, the error and every log line SHALL
NOT contain the explainer's API key. This SHALL hold whatever the user typed, and
for every source of settings. The error SHALL still name the setting that is
wrong, such as `explainer.api_key`, and say what is wrong with it.

Once the configuration is valid, the process SHALL keep the API key hidden when
it prints or logs its settings. It SHALL use the key's value only to call the LLM
provider.

#### Scenario: An API key that is not text is rejected without its value

- **WHEN** `config.yaml` sets `explainer.api_key` to a number, such as `12345`
- **THEN** the process stops with a configuration error that names
  `explainer.api_key`
- **AND** neither the error nor the log contains `12345`

#### Scenario: A misspelled key beside the API key does not show its value

- **WHEN** the `explainer` block in `config.yaml` holds an unknown key, such as
  `apikey`, set to a secret
- **THEN** the process stops with a configuration error that names the unknown
  key
- **AND** neither the error nor the log contains the secret

#### Scenario: An explainer block that is not a mapping does not show its value

- **WHEN** `config.yaml` sets `explainer` to a list or text that holds a secret
- **THEN** the process stops with a configuration error that says `explainer`
  must be a mapping of settings
- **AND** neither the error nor the log contains the secret

#### Scenario: A valid API key is hidden when the settings are printed

- **WHEN** the configuration is valid and sets an explainer API key
- **AND** the process prints or logs its settings
- **THEN** the output does not contain the API key
