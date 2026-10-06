## Why

Most Home Assistant OS users run the Mosquitto broker add-on. Today they must copy
its host name and a broker password into PierPressure's `config.yaml` by hand. The
Supervisor already holds those settings and hands them to any add-on that asks for
the `mqtt` service. Using them is the setup people expect from a Home Assistant
add-on, and it keeps a password out of the config file.

Story: #28 `ha-addon-mqtt-service`.

## What Changes

- **The add-on asks for the `mqtt` service.** `ha-addon/config.yaml` declares
  `services: [mqtt:want]`. `want` means the add-on still installs when no add-on
  provides the service, so users with another broker are not blocked.
- **The service reads the broker from the Supervisor when the file names none.**
  Inside an add-on, the Supervisor sets `SUPERVISOR_TOKEN`. When that variable is
  set and `config.yaml` has no `mqtt.host`, the service asks the Supervisor for the
  `mqtt` service. It then uses that broker's host, port, username and password.
- **The file's broker settings win as a group.** When `config.yaml` sets
  `mqtt.host`, the file supplies the host, port, username and password, and the
  Supervisor is not asked. So the Supervisor's credentials only ever go to the
  broker that issued them. `discovery_prefix` and `base_topic` always come from
  the file.
- **The `mqtt:` block becomes optional in the add-on.** A file with no `mqtt:`
  block works when the Supervisor provides a broker.
- **The service waits briefly for the broker's details.** The Mosquitto add-on
  removes and re-registers its service details each time it starts. So at boot the
  details can be missing for a few seconds. The service retries the request for a
  bounded time before it gives up.
- **Clear errors when no broker can be found.** If the file names no host and the
  Supervisor has no `mqtt` service after the wait, the service stops. Its error
  says to install the Mosquitto add-on or to set `mqtt.host`. If the Supervisor
  refuses the add-on access, the service stops at once with an error that says
  so. If the Supervisor's broker requires TLS, or an MQTT version other than
  3.1.1, the service stops with an error, because PierPressure supports neither
  yet.
- **The log names the broker's source.** It logs where the broker settings came
  from, and the host and port. It never logs the password.
- **Document it.** `ha-addon/DOCS.md` and the README's add-on section explain that
  a Mosquitto user can leave the `mqtt:` connection settings out.

Out of scope:

- Any change outside the add-on. Without `SUPERVISOR_TOKEN`, a Docker or source
  install behaves exactly as it does today, and still requires `mqtt.host`.
- Finding brokers other than the one the Supervisor provides.
- TLS connections, and MQTT versions other than 3.1.1, for any broker.
- Retrying the broker connection itself. That is #33.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the add-on asks the Supervisor for the `mqtt` service and uses that
  broker when `config.yaml` names none. This replaces "the file includes the MQTT
  broker settings" and adds behaviour that runs only inside the add-on.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: declares the `mqtt` service.
  - `pierpressure/core/config.py`: config loading splits into two pure steps.
    The first reads the file and says whether it names a broker host. The second
    builds the config, and accepts broker settings to use when the file names
    none. The core does no network access and calls no code that does.
  - `pierpressure/__main__.py`: between the two steps, asks the Supervisor for
    the broker, only when `SUPERVISOR_TOKEN` is set and the file names no host.
  - `ha-addon/DOCS.md` and `README.md`: the add-on setup.
- **New code:** a small Supervisor client outside `pierpressure/core/`, using
  `httpx`, which is already a dependency.
- **Tests:** the precedence rule, the wait and its time limit, the TLS, MQTT
  version, "access refused" and "no broker" errors, relative horizon files, the
  add-on config's `services` entry, that proxy settings never receive the
  Supervisor token, and that Docker behaviour is unchanged.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
