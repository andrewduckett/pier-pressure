## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required behaviour.
This design covers how the service finds the Supervisor's broker without breaking
the pure core.

Facts that shape the approach:

- **The Supervisor's API.** An add-on reads a service with
  `GET http://supervisor/services/mqtt` and the header
  `Authorization: Bearer $SUPERVISOR_TOKEN`. The Supervisor checks only that the
  add-on declared the service. The add-on needs no `hassio_api` permission
  (`supervisor/api/middleware/security.py`, `supervisor/api/services.py`).
- **The response.** On the maintainer's instance (Supervisor 2026.09.3,
  Mosquitto 7.1.1), the response was
  `{"result":"ok","data":{"host":"core-mosquitto","port":1883,"ssl":false,
  "protocol":"3.1.1","username":"addons","password":"…","addon":"core_mosquitto"}}`.
  The `/v2/services/mqtt` path renames `addon` to `app`. PierPressure reads
  neither key.
- **No provider.** When no add-on provides the service, the Supervisor answers
  with an error result, "Service not enabled".
- **Mosquitto withdraws its details on every start.** Its `discovery` script waits
  for port 1883, deletes its `mqtt` registration, then publishes it again. The
  details are always `port: 1883, ssl: false`, even when TLS listeners are on.
- **Only add-ons get the token.** The Supervisor sets `SUPERVISOR_TOKEN` in every
  add-on container (`supervisor/docker/app.py`). Docker and source installs never
  have it.
- **`load_config` is in the core.** `pierpressure/core/config.py` must not import
  Home Assistant code or reach the network. A test enforces the import boundary.
  `MqttConfig.host` is required today.
- **Tests run offline.** `tests/offline_guard.py` makes any real connection fail.
  The weather providers already accept an injected `httpx.Client`.

## Goals / Non-Goals

**Goals:**

- The core stays pure. The only network access lives outside
  `pierpressure/core/`.
- The service asks the Supervisor only when the file names no host. A user with
  their own broker never triggers a request.
- Tests cover the wait without real sleeping and without network access.

**Non-Goals:**

- Watching for later changes to the Supervisor's broker details. The service reads
  them once, at startup.
- Supporting MQTT versions other than 3.1.1, or TLS. The Mosquitto add-on always
  reports `3.1.1` without TLS. D5 refuses anything else with a clear error.
- A hard wall-clock limit on a single request. The Supervisor is a trusted local
  service, so each request's own timeout is enough (D4).
- Sharing a back-off with #33. That story may reuse or replace this wait.

## Decisions

### D1. `SUPERVISOR_TOKEN` decides whether the service is inside an add-on

`__main__` treats a set, non-empty `SUPERVISOR_TOKEN` as "running inside an
add-on". Without it, the service never asks the Supervisor, so behaviour is
exactly as before.

- *Why:* the Supervisor sets the token in every add-on, and nothing else sets it.
  Checking it needs no network access.
- *Alternative:* an explicit setting such as `PIERPRESSURE_SUPERVISOR=1` in the
  add-on's `environment`. Rejected: it adds a setting that has to agree with the
  token anyway, because the request needs the token.

### D2. Config loading splits into two pure steps, and the edge looks up between them

The core never calls code that reaches the network. ADR-0005 requires the core to
receive data, not an interface that fetches it. So config loading splits in two:

1. `read_config(path)` reads the YAML file and expands `${VAR}`. It returns a
   small value that holds the raw config and the folder that holds the file. It
   also reports whether the file's `mqtt` block names a `host`. This step reads
   only the file and the environment, as `load_config` does today.
2. `build_config(read, broker=None)` validates the raw config and returns
   `AppConfig`. `broker` is plain data: host, port, username and password.
   Relative horizon `file:` paths still resolve against the config file's
   folder, which the value from step 1 carries. The existing test for this in
   `tests/test_horizon_config.py` must keep passing unchanged.

`__main__` runs step 1. If `SUPERVISOR_TOKEN` is set and the file names no host,
it asks the Supervisor for the broker (D3). Then it runs step 2 with the result.
`load_config(path)` stays, as `build_config(read_config(path))`, so its current
callers and tests keep working.

`build_config` applies the precedence rule from the spec:

1. The file sets `mqtt.host`: build `MqttConfig` from the file alone, and ignore
   any `broker` argument.
2. The file sets `mqtt.port`, `mqtt.username` or `mqtt.password` without
   `mqtt.host`: raise `ConfigError`, telling the user to set `mqtt.host` too.
   `read_config` checks this too, so the add-on stops before it asks the
   Supervisor.
3. No host and no `broker`: validate as today, so the missing-host error stays the
   same.
4. No host and a `broker`: merge its four settings into the file's `mqtt` block.
   `discovery_prefix` and `base_topic` keep the file's values or defaults. The
   `mqtt:` block itself may be missing.

A Supervisor failure raises an error that `__main__` logs as a
"Configuration error", then exits with status 1, as it does for other config
errors.

- *Why:* the edge does all network access, and the core only receives data. The
  service only asks the Supervisor when the file names no host. The core still
  owns parsing and `${VAR}` expansion, so nothing is duplicated.
- *Alternative:* `load_config(path, broker_lookup)` with an injected callable that
  the core calls only when needed. Rejected: the core would then trigger network
  access. ADR-0005 rejects exactly that, and the import-boundary test cannot catch
  it.
- *Alternative:* `__main__` always asks the Supervisor first and passes plain
  settings in. Rejected: it would ask, and maybe wait up to 60 seconds, even when
  the file names its own broker.

### D3. A small Supervisor client lives in `pierpressure/supervisor.py`

The new module sits beside `health.py`, outside the core. It exposes one function
that returns the broker's connection settings or raises an error. It takes an
`httpx.Client`, a sleep function and a monotonic clock as optional arguments, so
tests inject an `httpx.MockTransport` and a fake clock.

Each request has an `httpx` timeout of 5 seconds. The production client is built
with `trust_env=False`. By default, `httpx` sends requests through any proxy named
in `HTTP_PROXY` or `ALL_PROXY`, and that proxy would see the Supervisor token. A
test sets those variables and checks that the request still goes straight to the
Supervisor. The client reads `data.host`,
`data.port`, `data.username`, `data.password`, `data.ssl` and `data.protocol`. `username` and `password` may be
missing; the client passes them on as `None`.

- *Why:* a module of its own keeps Supervisor knowledge in one place, and keeps
  `__main__` short. `httpx` is already a dependency.

### D4. The client retries for 60 seconds, except when access is refused

The client tries once, then pauses 2 seconds between tries. It starts no new
request later than 60 seconds after the first one. It shortens the last pause so
that it does not end past that point. Each request keeps its own 5-second timeout
(D3), so the whole wait ends within about 65 seconds.

An `httpx` timeout limits each step of a request, such as connecting or reading
one chunk, not the request as a whole. So a server that kept sending small chunks
could hold one request open for longer. The Supervisor is a trusted local
service, so the design accepts that risk rather than add a separate wall-clock
cut-off.

The Supervisor answers "Service not enabled" with HTTP 400, a bad token with 401,
and an undeclared service with 403. The client treats the following cases as
"not available yet", and retries:

- HTTP 400, which is how the Supervisor says "Service not enabled"
- HTTP 404, or any 5xx status
- a connection error or timeout
- a response that is not valid JSON, or has no usable `host` and `port`

It treats HTTP 401 and 403 as "access refused", and fails at once. Waiting cannot
fix a bad token or a missing service declaration, and installing Mosquitto will
not either. That error says the Supervisor refused access to the `mqtt` service,
and tells the user to set `mqtt.host` and to report the problem.

After the deadline, the client raises an error that says no MQTT broker was found.
The message tells the user to install the Mosquitto broker add-on, or to set
`mqtt.host` in `config.yaml`. The client logs one line at the first miss, so a
user who watches the log sees why startup is slow.

- *Why:* the Mosquitto add-on withdraws its details for a few seconds on each
  start, so a short wait covers a reboot. An access failure means the add-on
  itself is wrong, so it gets its own message and no wait.
- *Alternative:* fail at once, and leave all waiting at startup to #33. Rejected:
  this change would then add a new way to fail at boot for the very users it
  serves.
- *Alternative:* stop at once on "Service not enabled", because that may mean no
  Mosquitto add-on is installed. Rejected: Mosquitto returns the same answer while
  it restarts, so the two cases cannot be told apart.

### D5. A broker that needs TLS or another MQTT version is refused at once

The client checks two fields, and raises an error at once for either. It does not
retry.

- **`ssl: true`.** The message says the broker requires TLS, which PierPressure
  does not support. It tells the user to set `mqtt.host` and `mqtt.port` in
  `config.yaml` to a broker listener that accepts connections without TLS.
- **`protocol` other than `3.1.1`.** The Supervisor's schema also allows `3.1`.
  The message names the version and says PierPressure supports only 3.1.1. It
  tells the user to set `mqtt.host` and `mqtt.port` to a broker that accepts
  3.1.1. A missing `protocol` counts as `3.1.1`, the Supervisor's default.

- *Why:* the Mosquitto add-on never reports TLS or version 3.1, so these checks
  guard only against other providers. Connecting without TLS would quietly drop
  the encryption the provider asked for, and send its credentials in plain text.
- *Alternative:* support MQTT 3.1 by passing the version to paho. Rejected: it
  adds a protocol setting to the delivery code for a provider nobody here uses.

### D6. The log names the source, never the password

After it loads the config, `__main__` logs one line with the broker's source and
its `host:port`. Examples: `MQTT broker from the Supervisor's mqtt service:
core-mosquitto:1883`, and `MQTT broker from config.yaml: broker.lan:1883`. No log
line and no error message includes the password or the token.

## Risks / Trade-offs

- [Startup is up to about 65 seconds slower when no broker add-on is installed and the
  file names no host.] → The first miss logs a line that explains the wait. The
  final error says how to fix it.
- [The Supervisor's API could change shape.] → The client reads six fields from
  a path that has been stable across API versions. A response that is not JSON,
  or lacks a host and port, counts as "not available yet" (D4). After the
  deadline, the user gets the "no MQTT broker found" error.
- [An existing add-on user whose file sets `host: core-mosquitto` gets nothing
  new.] → That file keeps working, unchanged. The add-on docs explain that leaving
  out `host` uses the Supervisor's broker.
- [Mosquitto could replace its `addons` password while PierPressure runs.] → The
  password comes from Mosquitto's stored data and survives restarts. If it ever
  changes, restarting PierPressure picks up the new one. #44 covers reconnecting.

## Migration Plan

No migration. Existing config files keep working, because a file that sets
`mqtt.host` behaves as before. The change reaches add-on users through the usual
release and add-on version pull request. To roll back, the maintainer reverts the
add-on version to the previous release.

The archive step also updates the Purpose paragraph of
`openspec/specs/ha-addon/spec.md`. It now says the add-on "is packaging only" and
"adds no behaviour". After archive it must say that the add-on's only behaviour of
its own is to use the Supervisor's broker when the file names none. A delta spec
cannot change a Purpose, so `tasks.md` must include this as an explicit archive
task when it is written.
