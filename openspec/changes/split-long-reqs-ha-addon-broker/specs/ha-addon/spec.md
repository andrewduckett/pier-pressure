## ADDED Requirements

### Requirement: The add-on reads config.yaml from its own config folder

Inside an add-on, the service SHALL read `config.yaml` from the add-on's own
config folder when that file exists. The file adds settings to the Configuration
form, as the requirement "The add-on builds one set of settings from the form
and config.yaml" describes. In Home Assistant, the user finds that folder as
`/addon_configs/<repository-id>_pierpressure`.

#### Scenario: Add-on config mounts the folder

- **WHEN** the test suite reads the add-on config file
- **THEN** it maps `addon_config`
- **AND** it sets the environment variable `PIERPRESSURE_CONFIG` to
  `/config/config.yaml`


### Requirement: The add-on's config.yaml uses the same keys as outside Home Assistant

Inside an add-on, `config.yaml` SHALL use the same keys and values as outside
Home Assistant. It holds only the settings the Configuration form leaves unset.
So each of its piers needs only an `id` and the settings it adds. The file MAY
leave out the MQTT broker's connection settings, as the requirement "With no
broker host set, the connection settings come from the Supervisor" describes.

#### Scenario: Config file present

- **WHEN** the form lists the pier `backyard`
- **AND** the user has written a `config.yaml` in the add-on's config folder that
  sets `go_threshold` to 75 for `backyard`
- **AND** the user starts the add-on
- **THEN** the service publishes a verdict for `backyard` with a GO threshold of
  75


### Requirement: The add-on starts with the form's settings when config.yaml is missing

Inside an add-on, `config.yaml` is optional. When the Configuration form lists a
pier and the file does not exist, the add-on SHALL start with the form's
settings only.

#### Scenario: Config file missing

- **WHEN** the form lists a pier
- **AND** the add-on's config folder holds no `config.yaml`
- **THEN** the add-on starts
- **AND** it publishes a verdict for that pier


### Requirement: The add-on wants the Supervisor's mqtt service but does not need it

The add-on SHALL ask Home Assistant's Supervisor for the `mqtt` service, as a
service it wants but does not need. So the add-on SHALL install and start when no
other add-on provides the service.

#### Scenario: Add-on config declares the service

- **WHEN** the test suite reads the add-on config file
- **THEN** its `services` list contains `mqtt:want`


### Requirement: A broker host in config.yaml sets all four connection settings

The connection settings are the broker's host, port, username and password.
Inside an add-on, the service SHALL take all four from one source. When
`config.yaml` sets `mqtt.host`, all four SHALL come from the file, and the
service SHALL NOT ask the Supervisor for the broker. The form and the file cannot
both set connection settings, as the requirement "The broker connection and the
recompute interval each count as one setting" describes.

#### Scenario: The file's broker wins

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.host`
- **THEN** the service connects with the host, port, username and password from
  the file
- **AND** it does not ask the Supervisor for the broker


### Requirement: With no broker host set, the connection settings come from the Supervisor

Inside an add-on, when neither the Configuration form nor `config.yaml` sets
`mqtt.host`, the broker's host, port, username and password SHALL all come from
the Supervisor's `mqtt` service. When the Configuration form sets `mqtt.host`,
the requirement "A broker host on the form sets all four connection settings"
decides where all four come from.

#### Scenario: Mosquitto user leaves out the broker settings

- **WHEN** the Mosquitto add-on provides the `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the add-on's config folder holds no `config.yaml`, or one with no
  `mqtt:` block
- **THEN** the service connects to the broker host and port the Supervisor gave
- **AND** it logs in with the username and password the Supervisor gave
- **AND** it publishes under the default discovery prefix and base topic


#### Scenario: The log names the broker's source without the password

- **WHEN** the service uses the Supervisor's broker
- **THEN** its log says the broker came from the Supervisor's `mqtt` service, and
  names the host and port
- **AND** the log does not contain the broker password


### Requirement: The broker's topic settings come from config.yaml or their defaults

Inside an add-on, `mqtt.discovery_prefix` and `mqtt.base_topic` SHALL always
come from `config.yaml`, or from their defaults.

#### Scenario: The file sets only its topics

- **WHEN** the Supervisor provides an `mqtt` service
- **AND** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.base_topic` but not `mqtt.host`
- **THEN** the service connects with the Supervisor's connection settings
- **AND** it publishes under the file's base topic


### Requirement: A broker port or login in config.yaml without a host is rejected

Inside an add-on, a `config.yaml` that sets `mqtt.port`, `mqtt.username` or
`mqtt.password` without `mqtt.host` SHALL be rejected with a configuration error
that says to set `mqtt.host` too.

#### Scenario: Credentials without a host are rejected

- **WHEN** the form lists a pier and sets no broker field
- **AND** the user's `config.yaml` sets `mqtt.username` but not `mqtt.host`
- **THEN** the add-on stops
- **AND** its log contains a configuration error that says to set `mqtt.host`


### Requirement: Outside an add-on, the service does not ask the Supervisor for the broker

The service SHALL ask the Supervisor for the broker only when it runs inside an
add-on. Outside an add-on, `mqtt.host` SHALL stay required, and the service SHALL
behave as it did before the add-on could use the Supervisor's broker.

#### Scenario: Outside an add-on, nothing changes

- **WHEN** the service runs outside an add-on with a `config.yaml` that has no
  `mqtt.host`
- **THEN** it stops with the same configuration error as before this change
- **AND** it does not try to reach the Supervisor


### Requirement: Requests to the Supervisor bypass any proxy

The service SHALL send its requests, and the Supervisor's token, straight to the
Supervisor. It SHALL NOT send them through a proxy, even when the container's
environment names one.

#### Scenario: Proxy settings do not reach the token

- **WHEN** the container's environment sets `HTTP_PROXY` or `ALL_PROXY`
- **AND** the service asks the Supervisor for the broker
- **THEN** the request goes straight to the Supervisor, not through the proxy


### Requirement: The add-on keeps asking for a Supervisor broker that is not provided yet

When the service needs the Supervisor's broker and the Supervisor does not
provide it yet, the service SHALL keep asking. A Mosquitto add-on that is still
starting withdraws its service details for a few seconds, so a short wait covers
a reboot. These cases count as "not provided yet":

- The Supervisor says the service is not enabled.
- The request cannot connect, or it times out.
- The Supervisor returns a server error.
- The response has no usable host and port.

#### Scenario: Mosquitto is still starting

- **WHEN** the service starts while the Supervisor does not yet provide the `mqtt`
  service
- **AND** a request started within 60 seconds of the first returns usable broker
  details
- **THEN** the service uses the broker it gives and publishes a verdict for each
  pier


### Requirement: The wait for the Supervisor's broker lasts at most 60 seconds

While the service waits for the Supervisor's broker, it SHALL start no new
request later than 60 seconds after the first one. Each request SHALL have a
timeout of no more than 5 seconds. If a request started within those 60 seconds
returns usable broker details, the service SHALL use them and start normally.

#### Scenario: The wait ends on time

- **WHEN** the Supervisor provides no `mqtt` service
- **AND** each request to the Supervisor times out
- **THEN** the service starts no request later than 60 seconds after the first
- **AND** the add-on stops no later than 65 seconds after the first request


### Requirement: No Supervisor broker within 60 seconds stops the add-on

If no request started within 60 seconds of the first returns usable broker
details, the add-on SHALL stop with an error. The error SHALL say that no MQTT
broker was found. It SHALL tell the user to install the Mosquitto broker add-on,
or to set `mqtt.host` on the Configuration tab or in `config.yaml`. It SHALL NOT
say that `config.yaml` is not read.

#### Scenario: No broker add-on is installed

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** no request started within 60 seconds of the first returns usable broker
  details
- **THEN** the add-on stops
- **AND** its log says no MQTT broker was found
- **AND** it tells the user to install the Mosquitto broker add-on, or to set
  `mqtt.host` on the Configuration tab or in `config.yaml`
- **AND** it does not say that `config.yaml` is not read


### Requirement: A refused mqtt service stops the add-on at once

If the Supervisor refuses the add-on access to the `mqtt` service, the add-on
SHALL stop at once, without waiting. Its error SHALL say that the Supervisor
refused access to the `mqtt` service. It SHALL tell the user to set `mqtt.host`
on the Configuration tab or in `config.yaml`, and to report the problem. It SHALL
NOT say that `config.yaml` is not read.

#### Scenario: The Supervisor refuses access

- **WHEN** neither the form nor `config.yaml` sets `mqtt.host`
- **AND** the Supervisor refuses the add-on access to the `mqtt` service
- **THEN** the add-on stops at once, without waiting
- **AND** its log says the Supervisor refused access to the `mqtt` service
- **AND** it tells the user to set `mqtt.host` on the Configuration tab or in
  `config.yaml`, and to report the problem


### Requirement: The core checks each saved setting as it checks config.yaml

The core SHALL check every setting the add-on reads, as it checks the same
setting in `config.yaml`. The add-on SHALL NOT decide whether a setting's value
is valid. For each setting the form declares, it SHALL pass on any value it does
not expect, so the core can reject it. The Supervisor's check when the user saves
the form is a convenience, not a guarantee. A pier SHALL get the same result, and
an error that names the same setting, whether or not the Supervisor checked its
values.

#### Scenario: Values the Supervisor would refuse get the core's errors

- **WHEN** the saved form values list four piers
- **AND** one pier has a latitude of 95
- **AND** one pier has a `go_threshold` of 101
- **AND** one pier has `horizon_points` saved as the number 5
- **THEN** the service logs an error for each of those three piers
- **AND** each error names the same setting as the error for a `config.yaml`
  pier with the same value: `latitude`, `go_threshold` and `horizon.points`
- **AND** it publishes a verdict for the fourth pier


### Requirement: The add-on only reads, renames and combines the saved form values

The add-on SHALL only read the saved form values, rename form fields to their
`config.yaml` names, and combine them with `config.yaml`. It SHALL ignore any
top-level key in the saved values that the form does not declare, as the
Supervisor does when it saves the form. The rules for combining the form with
`config.yaml` stay with the add-on, as the requirement "The add-on builds one
set of settings from the form and config.yaml" describes, because only the
add-on has two sources.

#### Scenario: The add-on renames form fields for the core

- **WHEN** the saved form values set `interval_seconds` to 600
- **AND** they list a pier with `min_altitude` set to 15
- **THEN** the core receives a `recompute` block whose `interval_seconds` is 600
- **AND** it receives that pier with a `horizon` block whose `min_altitude` is 15

### Requirement: A form field that is not set is left out before the core checks the pier

The add-on SHALL leave out any Configuration form field that is not set before
the core checks the pier, as the requirement "An empty or blank form field counts
as not set" describes. This rule says what an empty field means, not whether a
value is valid.

#### Scenario: A field saved as null is left out

- **WHEN** the saved form values list a pier with `max_gust` saved as null
- **THEN** the core receives that pier with no `max_gust` key

### Requirement: Saved form values of the wrong shape stop the add-on

Inside an add-on, the service SHALL stop with a configuration error when the
saved form values do not have the shape it needs to run:

- The saved values are not valid JSON, or their root is not a mapping.
- Their `piers` is not a list.

#### Scenario: Saved values that are not a mapping stop the add-on

- **WHEN** the saved form values are a list, not a mapping
- **THEN** the add-on stops with a configuration error that names the file of
  saved values


## MODIFIED Requirements

### Requirement: A broker host on the form sets all four connection settings

Inside an add-on, when the Configuration form sets `mqtt.host`, the host, port,
username and password SHALL all come from the form. The service SHALL NOT ask
the Supervisor for the broker. A port the form does not set SHALL be 1883. When
the form does not set `mqtt.host`, the requirements "A broker host in
config.yaml sets all four connection settings" and "With no broker host set, the
connection settings come from the Supervisor" decide where all four come from.

#### Scenario: The form's broker is used

- **WHEN** the form lists a pier and sets `mqtt.host` to `broker.lan`,
  `mqtt.port` to 1884, `mqtt.username` to `pier`, and `mqtt.password`
- **THEN** the service connects to `broker.lan` on port 1884
- **AND** it logs in with the username `pier` and the form's password
- **AND** it does not ask the Supervisor for the broker


#### Scenario: The form's broker uses port 1883 by default

- **WHEN** the form lists a pier and sets `mqtt.host` but not `mqtt.port`
- **THEN** the service connects to that host on port 1883


## REMOVED Requirements

### Requirement: The add-on reads config from its own config folder

**Reason**: It bundled three behaviors. It is split into "The add-on reads
config.yaml from its own config folder", "The add-on's config.yaml uses the same
keys as outside Home Assistant" and "The add-on starts with the form's settings
when config.yaml is missing". Its 3 scenarios move word for word. Its pointer to
"The add-on combines the Configuration form with config.yaml", a heading that
was already removed, now names "The add-on builds one set of settings from the
form and config.yaml".

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The add-on uses the Supervisor's MQTT broker when the settings name none

**Reason**: It bundled seven behaviors. It is split into "The add-on wants the
Supervisor's mqtt service but does not need it", "A broker host in config.yaml
sets all four connection settings", "With no broker host set, the connection
settings come from the Supervisor", "The broker's topic settings come from
config.yaml or their defaults", "A broker port or login in config.yaml without a
host is rejected", "Outside an add-on, the service does not ask the Supervisor
for the broker" and "Requests to the Supervisor bypass any proxy". Its 8
scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The add-on waits a bounded time for the Supervisor's broker

**Reason**: It bundled four behaviors. It is split into "The add-on keeps asking
for a Supervisor broker that is not provided yet", "The wait for the
Supervisor's broker lasts at most 60 seconds", "No Supervisor broker within 60
seconds stops the add-on" and "A refused mqtt service stops the add-on at once".
Its 4 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The core checks every saved setting

**Reason**: It bundled four behaviors. It is split into "The core checks each
saved setting as it checks config.yaml", "The add-on only reads, renames and
combines the saved form values", "A form field that is not set is left out
before the core checks the pier" and "Saved form values of the wrong shape stop
the add-on". Its 2 scenarios move word for word, and two scenarios are added so
that each new requirement has one. Its two pointers to "The add-on combines the
Configuration form with config.yaml", a heading that was already removed, now
name "An empty or blank form field counts as not set" and "The add-on builds one
set of settings from the form and config.yaml".

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
