## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required
behaviour. This design covers how the form's broker reaches the settings the
service already builds, and where the connection rule lives.

Facts that shape the approach:

- **The edge translates the form into the file's shape.** Here, "the edge" means
  the code outside the pure core that reads the add-on's form.
  `pierpressure/addon_options.py` turns `/data/options.json` into the mapping a
  `config.yaml` would hold (ADR-0020). `load_app_config` in
  `pierpressure/__main__.py` wraps that mapping in a `ConfigFile`.
- **The core already chooses the broker's source.** `ConfigFile.names_broker_host`
  says whether the settings name a host. When they do not, `load_app_config`
  asks the Supervisor, and `build_config` puts the Supervisor's four connection
  settings in place of the file's (ADR-0017).
- **The connection rule sits in the file reader.** `read_config` rejects a
  port, username or password set without a host. The form path builds its
  `ConfigFile` directly, so it never meets this rule.
- **The Supervisor needs the block in `options`.** The Supervisor rejects saved
  options that leave out a block its schema declares, unless the block's type
  ends in `?`. A block cannot be marked that way. Fields inside a block can.
  Source: `_check_missing_options` in `supervisor/apps/options.py` of
  home-assistant/supervisor.
- **The Supervisor supports the needed field types.** Its schema has `port` (1
  to 65535) and `password`, and the form shows a nested block as a section of
  fields. The `password` type hides the value on the form only. The Supervisor
  still writes the value as plain text to `/data/options.json`.
- **The delivery adapter sends any username that is not `None`.** In
  `pierpressure/delivery/mqtt.py`, an empty username still sets a login.

## Goals / Non-Goals

**Goals:**

- The form's broker reaches the core in the same shape as a file's `mqtt`
  block. The core gains no code that knows about the form.
- One connection rule for every source of settings, enforced in one place.

**Non-Goals:**

- Using the form's broker when the form lists no piers. Story #73 decides how
  the form and the file combine.
- Checks against values the Supervisor refuses to save. Story #83 removes the
  existing ones.

## Decisions

### D1. The form holds a nested `mqtt` block with the file's names

The form declares `mqtt` as a block of four optional fields: `host: str?`,
`port: port?`, `username: str?` and `password: password?`. The default in
`options` is an empty block, `mqtt: {}`.

The names match `config.yaml`. So the edge passes the block through without
renaming, and the log and error messages can name `mqtt.host` for both sources.
The block nests one level, within Home Assistant's limit of two.

`port` has no default on the form. A default would put a port into every saved
form. The connection rule would then count every form without a host as a
partial broker. The 1883 default stays in the core's `MqttConfig`.

Alternative considered: flat top-level fields such as `mqtt_host`. They also
fit the form, but they would need renaming at the edge and in every message.
The nested block needs neither.

### D2. The edge drops empty broker fields

When the form lists piers, `read_addon_options` copies the form's `mqtt` block
into the config-shaped mapping. It leaves out each field whose value is `None`,
empty text or blank text.

This is translation, not validation. A form field the user clears has no
setting behind it. Without this step, an empty username would reach the
delivery adapter and set an empty login. It would also count as a username set
without a host. The pier fields already treat blank `horizon_points` the same
way (addon-form-horizon).

When the form lists no piers, `read_addon_options` returns `None` as today. The
form's broker is then not read at all.

Alternative considered: treat blank values as unset in the core, for both
sources. That would change how an existing `config.yaml` loads. The proposal
keeps the file format unchanged.

### D3. The connection rule moves onto `ConfigFile`

The two checks in `read_config` move into `ConfigFile.__post_init__`:

- The `mqtt` value, when present, is a mapping.
- A port, username or password is not set without a host.

Every `ConfigFile` then meets the rule, whether `read_config` builds it from a
file or `load_app_config` builds it from the form. The error message stays the
same, and so does the order of checks for the file. The rule still runs before
the Supervisor is asked, so a bad form fails at once, not after the wait of up
to 60 seconds.

```
 config.yaml  --> read_config() -------+
                                       +--> ConfigFile(...)   connection rule
 options.json --> read_addon_options() +        |
                                                v
                              names_broker_host? --no--> ask the Supervisor
                                                |
                                                v
                                          build_config()
```

Alternative considered: run the rule in `build_config`. That runs after the
Supervisor is asked, so a bad form would fail only after the wait.

Alternative considered: repeat the rule in `read_addon_options`. That would
write the same rule twice, in two layers.

### D4. Advice follows where the broker came from

`build_delivery_and_explainer` picks the login advice from the broker's source,
not from the settings' source:

| Settings from | Broker from | Login advice |
|---|---|---|
| form | form | the adapter's default: check `mqtt.username` and `mqtt.password` |
| form | Supervisor | restart Mosquitto, or set the broker on the Configuration tab |
| file | Supervisor | restart Mosquitto, or set `mqtt.host` (unchanged) |
| file | file | the adapter's default (unchanged) |

`FORM_NOTE` changes its advice. Today it tells a form user to move their piers
into `config.yaml` to set `mqtt.host`. It will say that `config.yaml` is not
read while the form lists piers, and that the broker is set on the
Configuration tab. `load_app_config` already adds this note to every Supervisor
error on the form path, so `pierpressure/supervisor.py` does not change.

### D5. The log names the Configuration tab as the source

`load_app_config` logs the broker's source as one of three: the Supervisor's
`mqtt` service, the Configuration tab, or the config file's name. Today a form
broker would be logged as coming from `config.yaml`, which the service did not
read. The log line keeps its form: source, host and port, with no password.

## Risks / Trade-offs

- [The `password` field hides the value on the form only] → `DOCS.md` says the
  value is stored by the Supervisor, not written into `config.yaml`. It does not
  claim the value is encrypted.
- [A form broker set while the form lists no piers is ignored with no log line]
  → Accepted. Story #73 settles how the form and the file combine. `DOCS.md`
  says the broker fields apply only when the form lists piers.
- [The Supervisor's form may show the empty `mqtt` block differently across Home
  Assistant versions] → The live check on Home Assistant OS confirms the block
  shows four fields, saves when empty, and saves a password.
- [Moving the rule onto `ConfigFile` lets any caller trigger it at
  construction] → The only callers are `read_config` and `load_app_config`, and
  no test builds a `ConfigFile` directly.

## Migration Plan

None. Nobody runs the add-on yet, and a `config.yaml` that loads today loads the
same way.
