## Why

PierPressure stops for good when it cannot reach the MQTT broker at startup. After
Home Assistant OS restarts, the PierPressure add-on can start before the Mosquitto
add-on accepts connections. The add-on then stays stopped, with no verdicts, until
someone starts it by hand. This breaks the rule that the core owns its own
freshness.

Story: #33 "Retry the broker connection at startup instead of exiting".

## What Changes

- **PierPressure keeps trying to reach the broker at startup.** When the broker
  cannot be reached, PierPressure tries again after a pause. The pause starts at
  1 second and doubles after each failure, up to 120 seconds. It keeps trying until
  the broker accepts the connection.
- **The paho library does the retrying.** PierPressure starts the connection in
  the background with paho, which already retries a failed first connection. The
  same paho mechanism handles reconnects after an outage, so PierPressure has one
  retry mechanism, not two.
- **The startup order does not change.** PierPressure publishes nothing until the
  broker accepts the connection. Then it publishes the provider health reset, then
  its `online` availability, as it does today.
- **The log shows each failed attempt.** While PierPressure waits, Home Assistant
  shows its entities as unavailable, because PierPressure has never gone online.
- **A rejected login still stops PierPressure.** When the broker rejects the
  username or password, or says the client is not authorized, retrying cannot
  help. PierPressure stops with an error that says the broker rejected its login.
- **Every install gets this.** The fix applies to the add-on, Docker, and source
  installs alike.
- **Document it.** `ha-addon/DOCS.md` explains the wait and the new error.

Out of scope:

- Restoring delivery after a reconnect: publishing `online` again and subscribing
  to the refresh commands again. That is #44. This change adds the `on_connect`
  handler that #44 will extend.
- A stopped process that stays "online" in Home Assistant. That is #41.
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
    an unreachable broker stops the process.
  - `tests/conftest.py`: the fake client can fail a number of attempts, then
    accept or reject the connection.
  - `ha-addon/DOCS.md`: the wait, and a row for the rejected-login error.
- **Tests:** the wait succeeds after failed attempts, nothing is published before
  the broker accepts, the startup order is unchanged, each failed attempt is logged,
  and a rejected login stops the process without going online.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
- **No new dependencies.**
