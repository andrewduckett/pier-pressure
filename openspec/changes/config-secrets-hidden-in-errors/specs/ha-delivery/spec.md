## ADDED Requirements

### Requirement: A configuration error never shows the broker password

When the process rejects its configuration, the error and every log line SHALL
NOT contain the broker password. This SHALL hold whatever the user typed, and for
every source of settings: `config.yaml`, the add-on's Configuration form, or both
combined. The error SHALL still name the setting that is wrong, such as
`mqtt.password`, and say what is wrong with it.

Once the configuration is valid, the process SHALL keep the password hidden when
it prints or logs its settings. It SHALL use the password's value only to log in
to the broker.

#### Scenario: A password that is not text is rejected without its value

- **WHEN** `config.yaml` sets `mqtt.password` to a number, such as `98765`
- **THEN** the process stops with a configuration error that names `mqtt.password`
- **AND** neither the error nor the log contains `98765`

#### Scenario: A misspelled key beside the password does not show its value

- **WHEN** the `mqtt` block in `config.yaml` holds an unknown key, such as
  `pasword`, set to a secret
- **THEN** the process stops with a configuration error that names the unknown
  key
- **AND** neither the error nor the log contains the secret

#### Scenario: An mqtt block that is not a mapping does not show its value

- **WHEN** `config.yaml` sets `mqtt` to a list or text that holds a secret
- **THEN** the process stops with a configuration error that says `mqtt` must be
  a mapping of settings
- **AND** neither the error nor the log contains the secret

#### Scenario: The add-on's combined settings do not show the password

- **WHEN** the add-on combines its Configuration form with `config.yaml`
- **AND** the combined `mqtt` block fails validation, while the form or the file
  sets a password
- **THEN** the add-on stops with a configuration error
- **AND** neither the error nor the log contains the password

#### Scenario: A valid password is hidden when the settings are printed

- **WHEN** the configuration is valid and sets a broker password
- **AND** the process prints or logs its settings
- **THEN** the output does not contain the password
