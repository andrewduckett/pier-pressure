## Why

PierPressure stops for good when its first attempt to connect to the MQTT broker
fails. After Home Assistant OS restarts, the PierPressure add-on can start before
the Mosquitto add-on accepts connections. The add-on then stays stopped, with no
verdicts, until someone starts it by hand. This breaks the rule that the core owns
its own freshness.

Story: #33 "Retry the broker connection at startup instead of exiting".

## What Changes

- **PierPressure keeps trying to connect at startup.** When an attempt fails,
  PierPressure pauses, then tries again. The pauses grow after repeated failures,
  up to 120 seconds. It keeps trying until the broker accepts the connection.
- **The paho library does the retrying.** PierPressure starts the connection in
  the background with paho, which already retries a failed first connection. The
  same paho mechanism handles reconnects after an outage. So PierPressure has one
  retry mechanism, not two.
- **The startup order does not change.** PierPressure publishes nothing until the
  broker accepts the connection. Then it publishes the provider health reset, then
  its `online` availability, as it does today.
- **The log shows each failed attempt.** It names the broker's host and port, but
  never the password.
- **A rejected login still stops PierPressure.** The broker can refuse because the
  username or password is wrong, or because the client is not authorized.
  Retrying cannot fix either. PierPressure stops with an error that says the
  broker rejected its login.
- **Every install gets this.** The fix applies to the add-on, Docker, and source
  installs alike.
- **Document it.** `ha-addon/DOCS.md` explains the wait and the new error.

Why the add-on's 60-second wait for the Supervisor's broker does not get in the
way: the Supervisor keeps the Mosquitto add-on's broker settings across a reboot.
So at boot, PierPressure gets the settings at once. Only its connection to the
broker fails, and this change retries that.

Out of scope:

- Restoring delivery after a reconnect: publishing `online` again and subscribing
  to the refresh commands again. That is #44. This change adds the `on_connect`
  handler that #44 will extend.
- A stopped process that stays `online` in Home Assistant. That is #41. Until it
  is fixed, entities can show the `online` state left by an earlier run while
  PierPressure waits for the broker.
- A failed publish that stops PierPressure. That is #43.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: adds a requirement that the service waits for the broker at
  startup instead of exiting, and stops only when the broker rejects its login.

## Impact

- **Changed files:**
  - `pierpressure/delivery/mqtt.py`: `MqttDelivery.connect` starts the connection
    in the background and waits for the broker to accept it. It raises
    `DeliveryError` only when the broker rejects the login. The `MqttClient`
    protocol gains the paho calls and callbacks this uses.
  - `pierpressure/__main__.py`: the docstring and error message no longer say that
    a failed connection stops the process.
  - `tests/conftest.py`: the fake client can fail a number of attempts, then
    accept or reject the connection.
  - `ha-addon/DOCS.md`: the wait, and a row for the rejected-login error.
- **Tests** cover these cases:
  - The wait ends when the broker accepts after failed attempts.
  - Nothing is published before the broker accepts.
  - The startup order is unchanged.
  - Each failed attempt is logged.
  - A rejected login stops the process without going online.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
- **No new dependencies.**
