## Context

See proposal.md for why, and `specs/ha-delivery/spec.md` for the required
behaviour. This design covers how `MqttDelivery.connect` waits for the broker.

Facts that shape the approach:

- **Today's connect is one blocking attempt.** `MqttDelivery.connect`
  (`pierpressure/delivery/mqtt.py`) calls `will_set`, then paho's blocking
  `connect()`, then `loop_start()`. `connect` turns a socket error into
  `DeliveryError`, and `main` returns 1.
- **Today, PierPressure ignores the broker's answer.** paho's blocking `connect()`
  returns once the socket opens. The broker's answer (CONNACK) arrives later, on
  paho's network thread. No handler listens for it, so PierPressure never reports
  a wrong password.
- **paho 2.1.0 already retries a first connection.** `uv.lock` pins paho-mqtt
  2.1.0. Its `loop_start()` thread runs `loop_forever(retry_first_connection=True)`.
  After `connect_async()`, that thread behaves like this:
  - When the socket cannot open, paho calls `on_connect_fail`, waits, and tries
    again.
  - When the broker refuses, paho calls `on_connect` with the refusal's reason
    code. It then closes the socket, calls `on_disconnect`, waits, and tries again.
  - When the broker closes the connection before it answers, paho calls only
    `on_disconnect`, then waits and tries again.
  - The wait starts at `min_delay` and doubles up to `max_delay`, both set by
    `reconnect_delay_set`. paho resets the wait only after the broker accepts.
  - The same loop handles reconnects after an outage.
- **paho waits twice before its second attempt.** After the first socket failure,
  paho waits `min_delay`, leaves its first-connection loop, then waits `2 *
  min_delay` before trying again. With delays of 1 and 120 seconds, the gaps
  between attempts are about 3, 4, 8, 16, 32, 64, then 120 seconds. The spec
  therefore sets bounds on the pauses, not an exact sequence.
- **paho maps MQTT 3.1.1 refusal codes to named reason codes.** Code 4 becomes
  "Bad user name or password" and code 5 becomes "Not authorized". paho
  recommends comparing reason codes by name, because the numbers differ between
  MQTT versions.
- **paho answers two refusals with an immediate try.** Both happen inside its
  CONNACK handler, before any `on_connect` call, and without a pause:
  - For code 1, "unsupported protocol version", paho switches to MQTT 3.1 and
    tries again. It does this only while its protocol is 3.1.1, so at most once.
  - For code 2, "identifier rejected", paho generates a client ID and tries again.
    It does this only while the client ID is empty, so at most once.
  The spec counts each immediate try as part of the attempt it follows.
- **An immediate try can end paho's thread.** If the immediate try cannot open a
  socket, the `OSError` escapes paho's loop and ends its thread. No handler runs.
  paho sets its `_thread` attribute back to `None`. A new `loop_start()` call then
  starts a fresh thread. That thread waits, as after any lost connection, then
  tries again with the same pauses.
- **The Supervisor keeps the broker's settings across a reboot.** It stores the
  `mqtt` service in `services.json`. It removes it when the providing add-on is
  uninstalled (`supervisor/apps/app.py`), or when an add-on calls its delete API.
  The Mosquitto add-on calls that API as it starts, then registers again a few
  seconds later. The existing 60-second wait covers that gap. So the 60-second Supervisor wait
  returns at once at boot, and the connection attempt is what fails.
- **The main thread owns all publishing** (ADR-0012). paho callbacks only hand
  work to the main thread.
- **The spec fixes the startup order** (provider-health-entities D4): the health
  reset, then `online`, then verdicts. `Service.run` does this after `connect`
  returns.
- **Tests run offline** with `FakeMqttClient` (`tests/conftest.py`). The fake
  records calls and can make `connect` raise.

## Goals / Non-Goals

**Goals:**

- `MqttDelivery.connect` returns only once the broker accepts the connection. It
  raises `DeliveryError` only for a rejected login.
- One retry mechanism serves the first connection now and reconnects later (#44).
- Tests cover the wait, the refusals and the logging without real sleeping.

**Non-Goals:**

- Restoring `online` and the refresh subscriptions after a reconnect (#44). The
  handlers ignore every call after the broker first accepts.
- Stopping on a rejected login during a *later* reconnect. #44 decides what to do
  about that case.
- A time limit on the startup wait. The spec asks the process to wait forever.
- Handling SIGTERM during the wait. The default signal action ends the process.
  That is correct, because the process has published nothing yet.
- Changing the Supervisor wait. The `ha-addon` capability owns it.

## Decisions

### D1. Let paho retry, with `connect_async` and `loop_start`

`connect` calls `will_set`, `reconnect_delay_set(1, 120)`, `connect_async(host,
port)`, then `loop_start()`. paho's thread then tries until the broker answers.

The code sets the delays explicitly, rather than relying on paho's defaults. The
spec bounds the pauses at 1 and 120 seconds, so the code states both numbers.

**Alternative: our own retry loop around the blocking `connect()`.** This would
copy the shape of `_wait_for_broker` in `pierpressure/supervisor.py`. The
blocking `connect()` returns before the CONNACK. So to see a rejected login, the
loop would still need an `on_connect` handler and a wait on paho's thread, as in
D2. We rejected it because it adds a second retry mechanism and saves no code:

- PierPressure would have two retry mechanisms: ours for the first connection,
  and paho's for every reconnect after it. Their pauses and logging could drift
  apart.
- It would still need the handlers and the wait from D2. It would add a loop, a
  back-off and a clock on top of them.

**Alternative: run `loop_forever` on our own thread.** This would let us catch
the thread ending. We rejected it because paho changes how `publish` writes when
`loop_start` did not start the thread. That would change the publishing path
ADR-0012 relies on.

### D2. The handlers hand one outcome to the main thread

`MqttDelivery` holds a `threading.Event` and an outcome slot. paho calls these
handlers on its thread:

- `on_connect` with a success code: store "accepted", then set the event.
- `on_connect` with "Bad user name or password" or "Not authorized": store
  "rejected" with that reason, then set the event.
- `on_connect` with any other refusal: log a failed attempt.
- `on_connect_fail`: log a failed attempt.
- `on_disconnect`: log a failed attempt only when no other handler has logged
  it. D4 explains how.
- `on_pre_connect`: start a new attempt for logging (D4).

Once the event is set, the handlers do nothing more. Later reconnects are #44's.

`connect` waits on the event in 1-second slices. On "accepted", `connect`
returns, and `Service.run` carries on as today. On "rejected", `connect` calls
`loop_stop()`, so paho stops trying, then raises `DeliveryError` with the message
from D3.

After each slice with no outcome, `connect` checks that paho's network thread is
still running. If the thread has ended, an immediate try has failed (see
Context). `connect` logs that attempt as a failed attempt, then calls
`loop_start()` again. The new thread pauses, then tries again, so the process
never exits on a failed attempt. `connect` restarts the thread at most once per
slice, so a thread that keeps ending cannot spin.

The handlers never publish, so ADR-0012 holds. `connect` returns before anything
is published, so the startup order holds without change.

paho exposes its thread only as the private attribute `_thread`. `MqttDelivery`
reads it in one helper. A test starts a real paho client with the offline guard
in place, and checks that the attribute holds a live thread. That test fails if
a paho upgrade renames it.

**Alternative: a queue, as for refresh commands.** A queue suits a stream of
events. Here there is exactly one outcome, so an event and a slot are simpler.

### D3. Compare reason codes by name, and name the fix in the error

The handler compares the reason code with "Bad user name or password" and "Not
authorized" through paho's `ReasonCode` equality, which compares names. paho
recommends this. It also keeps working if PierPressure moves to MQTT 5, where the
numbers are 134 and 135.

Each rejection gets its own advice:

- Bad user name or password: "The MQTT broker at host:port rejected the login:
  bad user name or password. Check `mqtt.username` and `mqtt.password`."
- Not authorized: "The MQTT broker at host:port rejected the login: not
  authorized. Check the MQTT user's permissions on the broker."

Inside the add-on, the Supervisor may have supplied the credentials. Then the
advice also says to check the Mosquitto add-on. `MqttDelivery` does not know
where the settings came from, so `main` adds that sentence when it logs the
error.

### D4. One log line per failed attempt

Each failed attempt logs a warning: "Could not connect to the MQTT broker at
host:port (reason); trying again". The line never includes the password. The
reason depends on the handler:

- `on_connect_fail`: the socket error's class name. paho passes no exception, so
  the handler reads it from `sys.exc_info()`. That works because paho calls the
  handler inside its `except OSError` block.
- `on_connect`: the refusal's reason name, such as "Server unavailable".
- `on_disconnect`: "connection closed before the broker answered".

paho also calls `on_disconnect` after a refusal and after a socket failure. Those
attempts are already logged. paho passes the same reason code, "Unspecified
error", in all three cases, so the code cannot tell them apart. Instead,
`MqttDelivery` keeps a flag that says the current attempt has been logged:

- paho calls `on_pre_connect` at the start of every attempt. Its handler clears
  the flag.
- `on_connect_fail` and a refusal in `on_connect` log the attempt and set the flag.
- `on_disconnect` logs the attempt only when the flag is clear, then sets it.

So each failed attempt gets exactly one line, whatever order paho's callbacks
come in. An immediate try (see Context) calls `on_pre_connect` again, which
clears the flag. That is correct, because the spec counts the immediate try as
part of the same attempt. If the immediate try ends the thread, `connect` logs
the attempt when it restarts the thread (D2).

A rejected login gets no "trying again" line. The error from D3 is the log line
for that attempt.

At the 120-second limit, the log gets about 30 lines an hour. That is acceptable
for a broker that is down.

### D5. The client protocol and the fake follow paho

The `MqttClient` protocol drops `connect`. It gains `connect_async`,
`reconnect_delay_set`, `on_pre_connect`, `on_connect`, `on_connect_fail` and
`on_disconnect`.

`FakeMqttClient` takes a script of attempt outcomes. An outcome is a socket
failure, a refusal with a reason name, a closed connection, or an acceptance. Its
`loop_start()` plays the script at once, on the calling thread, by calling the
handlers as paho would. The event is then set before `connect` waits, so tests
never block and never sleep. The fake records the delays passed to
`reconnect_delay_set`, so a test can check the 1 and 120. One extra script
outcome ends the fake's thread with no callback. A test uses it to check that
`connect` logs the attempt, starts the thread again, and then accepts.

The fake cannot show that real paho behaves as Context describes. Two focused
tests check that against the pinned paho source instead. Each drives a real paho
client with no network access. The offline guard blocks every connection, even
to the local machine. So each test replaces paho's private socket factory,
`_create_socket`, with one that returns one end of a `socket.socketpair()`. The
test plays the broker on the other end. One sends a code 1
CONNACK and checks that paho tries MQTT 3.1 at once without calling `on_connect`.
The other makes that immediate try fail and checks that the thread ends with
`_thread` set to `None`.

### D6. The entry point keeps its shape

`main` still catches `DeliveryError` from `connect` and returns 1. Only a rejected
login reaches that path now. The module docstring drops "or
the broker unreachable at boot". It says instead that the process waits for the
broker and stops only when the broker rejects its login.

## Risks / Trade-offs

- [A mistyped `mqtt.host` now waits forever instead of failing.] → Each attempt
  logs a warning that names the host and port. `ha-addon/DOCS.md` gets a row for
  that log line.
- [The fix relies on paho behaviour that its docs describe only briefly, and on
  one private attribute.] → `uv.lock` pins paho 2.1.0. A test pins the private
  attribute. A manual check against a broker that starts late confirms the
  behaviour before archive.
- [`FakeMqttClient` plays the script on one thread, so the tests do not exercise
  real thread timing.] → The handlers only log, store a value and set an event.
  Each of these is safe across threads. The manual check covers the real thread.
- [While PierPressure waits, Home Assistant can show the `online` state left by an
  earlier run.] → That is #41. This change publishes nothing while it waits, so it
  does not make that worse.
- [A login rejected during a later reconnect is only logged.] → This is #44's
  scope. Today that case already fails silently.
