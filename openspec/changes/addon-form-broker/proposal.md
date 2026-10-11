## Why

On the add-on's **Configuration** tab, a user cannot name an MQTT broker. A form
user therefore gets only the broker that the Supervisor hands out, which in
practice is the Mosquitto add-on. A user with any other broker must set up with
`config.yaml` instead, and type the broker password into that plain-text file.

This story adds the broker to the form, with the password in a password field.

Story: #72 `addon-form-broker`, part of epic #67.

## What Changes

- **A broker block on the form.** The form gains an optional `mqtt` block with
  four fields, named as in `config.yaml`:
  - `host`: the broker's host name or address.
  - `port`: the broker's port. Without it, the service uses 1883.
  - `username`: the login name, if the broker needs one.
  - `password`: the login password, in a field that hides its value.
- **The existing rule decides the source.** When the form lists piers and sets
  `host`, the service takes the host, port, username and password from the form,
  all four together. It does not ask the Supervisor. When `host` is not set, the
  service asks the Supervisor, as today (ADR-0017).
- **One connection rule for the file and the form.** A port, username or password
  without a host is an error, as it is in `config.yaml` today. The core now
  enforces this rule on the settings, whichever source they come from. Until
  now, only the config-file reader enforced it.
- **Advice that fits the source.** When the broker rejects a login from the
  form, the error points to the Configuration tab. Errors and advice no longer
  tell a form user to move their piers into `config.yaml` to choose a broker.
- **Empty fields count as not set.** A broker field the user clears on the form
  is treated as absent, not as empty text.
- **No password in the log.** The log names the Configuration tab as the
  broker's source. No log line or error message includes the password.
- **Documentation.** `ha-addon/DOCS.md` and the README's add-on section describe
  the broker fields. They no longer advise writing the broker password into
  `config.yaml` in the add-on.

Out of scope:

- A broker set on the form while the form lists no piers. The service then reads
  `config.yaml` as today, and the form's broker is not used. Story #73 decides
  how settings from the form and the file combine.
- TLS and MQTT versions other than 3.1.1. The add-on still refuses them.
- `discovery_prefix` and `base_topic` on the form. Their defaults stay.
- Removing the add-on layer's other checks of saved form values. Story #83 does
  that.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the Configuration form gains broker fields, and the rule that
  chooses between the form's broker and the Supervisor's broker now covers the
  form.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: an `mqtt` block in `options` and `schema`.
  - `ha-addon/translations/en.yaml`: labels and descriptions for the four fields.
  - `pierpressure/addon_options.py`: passes the form's `mqtt` block through,
    leaving out empty fields.
  - `pierpressure/core/config.py`: the connection rule moves from `read_config`
    onto `ConfigFile`, so every source of settings gets it.
  - `pierpressure/__main__.py`: the broker's source in the log, login advice,
    and the note added to a Supervisor error on the form path.
  - `ha-addon/DOCS.md` and `README.md`: the broker fields.
- **Unchanged:** the `config.yaml` format, and Docker and source installs. A
  `config.yaml` that loads today loads the same way.
- **Tests:** the manifest's new fields and labels, a form broker end to end, the
  connection rule on the form, and the advice for each broker source.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
