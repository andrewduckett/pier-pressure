## Context

See proposal.md for why, and `specs/ha-delivery/spec.md` for the required
behaviour. This design covers how `MqttDelivery.connect` waits for the broker.

Facts that shape the approach:

- **Today's connect is one blocking try.** `MqttDelivery.connect`
  (`pierpressure/delivery/mqtt.py`) calls `will_set`, then paho's blocking
  `connect()`, then `loop_start()`. A socket error becomes `DeliveryError`, and
  `main` returns 1.
- **Today, a rejected login fails silently.** `connect()` returns once the socket
  opens. The broker's answer (CONNACK) arrives later, on paho's network thread.
  Nothing listens for it, so a wrong password is never reported.
- **paho 2.1.0 already retries a first connection.** `uv.lock` pins paho-mqtt
  2.1.0. Its `loop_start()` thread runs `loop_forever(retry_first_connection=True)`.
  After `connect_async()`, that thread:
  - tries to open the socket, calls `on_connect_fail` on an `OSError`, waits, and
    tries again;
  - on a refused CONNACK, calls `on_connect` with the refusal's reason code, then
    returns `MQTT_ERR_CONN_REFUSED`, waits, and tries again;
  - waits `reconnect_delay_set(min_delay, max_delay)` seconds, doubling from
    `min_delay` up to `max_delay`. The defaults are 1 and 120.
  - The same loop handles reconnects after an outage.
- **paho maps MQTT 3.1.1 refusal codes to named reason codes.** Code 4 becomes
  "Bad user name or password" and code 5 becomes "Not authorized". paho
  recommends comparing reason codes by name, because the numbers differ between
  MQTT versions.
- **The main thread owns all publishing** (ADR-0012). paho callbacks only hand
  work to the main thread.
- **The startup order is in the spec** (provider-health-entities D4): the health
  reset, then `online`, then verdicts. `Service.run` does this after `connect`
  returns.
- **Tests run offline** with `FakeMqttClient` (`tests/conftest.py`). It records
  calls and can make `connect` raise.

## Goals / Non-Goals

**Goals:**

- `MqttDelivery.connect` returns only once the broker accepts the connection, and
  raises `DeliveryError` only for a rejected login.
- One retry mechanism serves the first connection now and reconnects later (#44).
- Tests cover the wait, the refusals and the logging without threads or sleeping.

**Non-Goals:**

- Restoring `online` and the refresh subscriptions after a reconnect (#44). The
  `on_connect` handler ignores every call after the first accepted connection.
- Stopping on a rejected login during a *later* reconnect. That case is logged
  only. #44 decides what to do about it.
- A time limit on the startup wait. The spec asks the process to wait forever.
- Handling SIGTERM during the wait. The default signal action ends the process,
  which is correct, because nothing has been published.

## Decisions

### D1. Let paho retry, with `connect_async` and `loop_start`

`connect` calls `will_set`, `reconnect_delay_set(1, 120)`, `connect_async(host,
port)`, then `loop_start()`. paho's thread then retries until the broker answers.

We set the delays explicitly. The spec states 1 and 120 seconds, so the code
states them too, rather than relying on paho's defaults.

**Alternative: our own retry loop around the blocking `connect()`.** This would
copy the shape of `_wait_for_broker` in `pierpressure/supervisor.py`. We rejected
it for two reasons:

- PierPressure would have two retry mechanisms: ours for the first connection,
  and paho's for every reconnect after it.
- The blocking `connect()` returns before the CONNACK. So our loop could never see
  a rejected login, and could not stop on one.

### D2. The callbacks hand one outcome to the main thread

`MqttDelivery` holds a `threading.Event` and an outcome slot. paho calls these
handlers on its thread:

- `on_connect` with a success code: store "accepted", set the event.
- `on_connect` with "Bad user name or password" or "Not authorized": store
  "rejected" with the reason name, set the event.
- `on_connect` with any other refusal: log it as a failed attempt. paho tries
  again.
- `on_connect_fail`: log a failed attempt. paho tries again.

Once the event is set, the handlers do nothing more. This leaves later reconnects
to #44.

`connect` waits on the event with no timeout. On "accepted" it returns, and
`Service.run` carries on as today. On "rejected" it calls `loop_stop()`, so paho
stops retrying, then raises `DeliveryError` with the login message from the spec.

The handlers never publish, so ADR-0012 holds. Nothing is published before
`connect` returns, so the startup order holds without change.

**Alternative: a queue, as for refresh commands.** A queue suits a stream of
events. Here there is exactly one outcome, so an event and a slot are simpler.

### D3. Compare reason codes by name

The handler compares the reason code's name, through paho's `ReasonCode`
equality, with "Bad user name or password" and "Not authorized". paho recommends
this. It also keeps working if PierPressure moves to MQTT 5, where the numbers
are 134 and 135.

### D4. One log line per failed attempt

Each failed attempt logs a warning: "Could not reach the MQTT broker at
host:port (reason); trying again". The reason is the socket error's class name
for an `on_connect_fail`, or the reason code's name for a refusal. The line never
includes the password. paho's `on_connect_fail` gets no exception, so the
handler reads the class name from `sys.exc_info()`. That is safe, because paho
calls the handler inside its `except OSError` block.

The first line is logged at once, and later lines follow paho's pauses. At the
120-second limit, that is about 30 lines an hour, which is acceptable for a
broker that is down.

### D5. The client protocol and the fake follow paho

The `MqttClient` protocol drops `connect` and gains `connect_async`,
`reconnect_delay_set`, `on_connect` and `on_connect_fail`.

`FakeMqttClient` takes a script of attempt outcomes: socket failures, refusals
with a reason name, and a final acceptance. Its `loop_start()` plays the script
at once, on the calling thread, by calling the handlers. The event is then set
before `connect` waits, so tests never block and never sleep. The fake records
the delays passed to `reconnect_delay_set`, so a test can check the 1 and 120.

### D6. The entry point keeps its shape

`main` still catches `DeliveryError` from `connect` and returns 1. Only the
rejected login reaches that path now. The module docstring drops "or the broker
unreachable at boot". It says instead that the process waits for the broker and
stops only when the broker rejects its login.

## Risks / Trade-offs

- [A mistyped `mqtt.host` now waits forever instead of failing.] → Each attempt
  logs a warning that names the host and port. `ha-addon/DOCS.md` gets a row for
  that log line. Home Assistant shows no PierPressure entities, or shows them as
  unavailable.
- [The fix relies on paho behaviour that its docs describe only briefly.] → The
  behaviour is in paho 2.1.0's source, and `uv.lock` pins that version. A manual
  check against a broker that starts late confirms it before archive.
- [`FakeMqttClient` plays the script synchronously, so the tests do not exercise
  real thread timing.] → The handlers only store a value and set an event, which
  is safe across threads. The manual check covers the real thread.
- [A login rejected during a later reconnect is only logged.] → This is #44's
  scope. Today that case already fails silently.
