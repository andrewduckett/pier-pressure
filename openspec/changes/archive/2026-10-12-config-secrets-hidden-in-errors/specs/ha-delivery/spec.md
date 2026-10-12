## ADDED Requirements

### Requirement: An error about the broker settings shows none of their text

When the process rejects the `mqtt` block, the error and the log SHALL NOT
contain any value from that block. They SHALL NOT contain the name of a key that
the block does not define either, because a user can type a secret where a key
name belongs. This SHALL hold for every source of settings: `config.yaml`, the
add-on's Configuration form, or both combined.

The error SHALL still say what is wrong:

- For a defined setting, it SHALL name the setting, such as `mqtt.port`, and
  state the rule the value broke.
- For a key the block does not define, it SHALL say that the block holds a
  setting it does not know, and list the settings the block defines.
- For an `mqtt` value that is not a mapping, it SHALL say that `mqtt` must be a
  mapping of settings.

This requirement covers errors about the `mqtt` block only. An error about a pier
still shows that pier's values, so a user can find a bad latitude or horizon.

Once the configuration is valid, the process SHALL show the broker password as a
mask whenever it prints or logs its settings. It SHALL use the password's value
only to log in to the broker.

#### Scenario: A password that is not text is rejected without its value

- **WHEN** `config.yaml` sets `mqtt.password` to a number, such as `98765`
- **THEN** the process stops with a configuration error that names
  `mqtt.password`
- **AND** neither the error nor the log contains `98765`

#### Scenario: An unknown key in the mqtt block is not named

- **WHEN** the process loads `config.yaml` on its own, outside the add-on
- **AND** the `mqtt` block holds a key it does not define, such as
  `pasword: hunter2`, or a bare key `hunter2`
- **THEN** the process stops with a configuration error that says the `mqtt`
  block holds a setting it does not know
- **AND** the error lists the settings the `mqtt` block defines
- **AND** neither the error nor the log contains `pasword` or `hunter2`

#### Scenario: An mqtt block that is not a mapping does not show its value

- **WHEN** `config.yaml` sets `mqtt` to a list or text that holds a secret
- **THEN** the process stops with a configuration error that says `mqtt` must be
  a mapping of settings
- **AND** neither the error nor the log contains the secret

#### Scenario: An unknown key with a value is not named in the add-on

- **WHEN** the add-on combines its Configuration form with `config.yaml`
- **AND** the file's `mqtt` block holds a key it does not define, with a value,
  such as `pasword: hunter2`
- **THEN** the add-on stops with a configuration error that says the `mqtt`
  block holds a setting it does not know
- **AND** neither the error nor the log contains `pasword` or `hunter2`

#### Scenario: The add-on's combined settings do not show the password

- **WHEN** the add-on combines its Configuration form with `config.yaml`
- **AND** the form sets a password
- **AND** the combined `mqtt` block fails validation, or the form and the file
  both set a broker setting
- **THEN** the add-on stops with a configuration error
- **AND** neither the error nor the log contains the password

#### Scenario: A valid password is masked when the settings are printed

- **WHEN** the configuration is valid and sets a broker password
- **AND** the process prints or logs its settings, at any stage of loading them
- **THEN** the output does not contain the password
