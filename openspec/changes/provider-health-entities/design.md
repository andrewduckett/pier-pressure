## Context

See proposal.md — Why. The requirements are in `specs/conditions/spec.md` and
`specs/ha-delivery/spec.md`.

`Service._publish` fetches conditions for one pier, produces the verdict, asks the
explainer for a narrative, and publishes. It fetches through `CompositeProvider.get`,
which the service sees as a `ConditionsProvider`: a function from a pier to
`Conditions`.

`CompositeProvider._safe_fetch` catches any error, logs it, and returns an empty
`SourceForecast`. That is where the knowledge of a failure is lost today. Nothing
after it can tell a failed fetch from an empty one, or say what went wrong.

Two facts about the providers shape the health attributes:

- Open-Meteo stamps its issue time at fetch (`issued_at=self.now()`). Its issue time
  and its last-success time come from the same fetch, moments apart at most.
- 7Timer! reports its model run time as its issue time. A 7Timer! payload with no
  `init` stamp parses to an empty forecast.

The narrative entity (ADR 0011) already set the pattern this change follows: an
additive entity beside the verdict document, filled at the edge, never read by the
core.

## Goals / Non-Goals

**Goals:**

- Carry each fetch's outcome from the provider layer to delivery without it ever
  passing through `produce_verdict`.
- Keep the health types free of anything conditions-specific, so another kind of
  provider could use them later.
- Keep every golden verdict byte-identical.

**Non-Goals:**

- A generic composite that merges any kind of provider. Each kind combines its
  sources differently, and only conditions needs one today.
- Health for the explainer provider. Its cache hits are not fetches, and its errors
  need their own redaction.

## Decisions

### D1 — The fetch returns its outcomes beside the conditions

`CompositeProvider.get` returns a `FetchResult`: the `Conditions` and one
`FetchOutcome` per provider it tried. A `FetchOutcome` holds the provider's key,
display name, role, the fetch time, whether it succeeded, the error, and the issue
time.

`_safe_fetch` builds the outcome. An exception gives a failed outcome. An empty
forecast also gives a failed outcome, with the error `no readings returned`. A
forecast with readings gives a successful outcome, whatever its blank fields.

The service unpacks the result. It passes only `conditions` to `produce_verdict`. So
"health never reaches the verdict" holds by structure, not by care.

- **Alternative considered:** inject a mutable health tracker into
  `CompositeProvider` and have the service read it after each fetch. It changes
  fewer signatures. But the data then flows by a side channel, and tests must set up
  shared state to see it. An explicit return value is easier to follow and test.

### D2 — Provider-neutral health types live in `pierpressure/health.py`

The new module holds `FetchOutcome`, `ProviderHealth`, and a pure function
`fold(previous, outcome) -> ProviderHealth`. It also holds `describe_error(exc)`,
which builds a safe error description (see D6).

`fold` applies these rules:

- A successful outcome sets `last_success` to the fetch time and `issued_at` to
  the outcome's issue time.
- A failed outcome keeps the earlier `last_success` and `issued_at`.
- Every outcome replaces the latest status, the latest fetch time, and the error.
  A success clears the error.

The module sits outside `pierpressure/core/`. Health describes the edge of the
system, and the core-boundary test keeps it that way. It also sits outside
`pierpressure/conditions/`, so nothing in it assumes weather.

- **Alternative considered:** `pierpressure/conditions/health.py`. It is closer to
  its only caller today. But it would have to move if the explainer ever reports
  health, and moving it later costs more than placing it well now.

### D3 — The service holds health in memory, per pier and provider

The service keeps a dictionary keyed by pier and provider key. On each publish it
folds that fetch's outcomes into the dictionary, then publishes the pier's health.

The service seeds the dictionary at startup with every configured provider, each
with no history. So discovery covers every configured provider, even one not tried
on a given publish.

The service also records `tracking_since`, the clock time when `run()` starts. Every
health record carries it. The README automation measures how long a sensor has been
unknown from this time (see D7).

### D4 — Startup resets health before the process goes online

Today `MqttDelivery.connect()` connects and then publishes the retained `online`
message. This change splits that in two:

1. `connect()` registers the last-will message and connects. It no longer publishes
   `online`.
2. A new `MqttDelivery.go_online()` publishes the retained `online` message.

`Service.run()` then starts in this order:

1. Publish the seeded health for every pier: discovery, a `None` state, and
   attributes with no history.
2. Call `delivery.go_online()`.
3. Fetch and publish every pier, as today.

So the old retained health is replaced before any entity can be online. The reset
waits on nothing but the broker, because no fetch or narrative call comes before it.
If the reset publish raises `DeliveryError`, `run()` stops before step 2. The process
then exits without publishing `online`.

A service with no health providers skips step 1 and goes online at once. The
existing "retained online availability while running" requirement still holds.

- **Alternative considered:** keep `online` in `connect()` and reset just after it.
  That leaves a window where Home Assistant shows the old success time as current.
  The window is short but unbounded if the reset publish stalls.

**Known limit (#41).** A clean disconnect does not trigger the last-will message, and
`_publish()` does not wait for the broker to confirm. So on a failed reset, the
retained availability keeps whatever value the previous run left. This change does
not make that worse. Issue #41 fixes it for every entity.

`CompositeProvider` exposes its providers (key, display name, role) so `__main__.py`
can pass them to the service. The default no-conditions provider has none, so a
service built without one publishes no health.

The fetch time comes from a `now` function injected into `CompositeProvider`.
`__main__.py` passes the service's `SystemClock`. Tests pass a fixed clock, so every
payload is deterministic.

Health is never written to disk. After a restart, every provider starts with no
history.

### D5 — A separate `publish_health` method in delivery

`MqttDelivery.publish_health(pier_id, healths)` publishes discovery, state, and
attributes for each health record. `publish_verdict` does not change. The service
calls `publish_health` for the startup reset (D4), and right after each
`publish_verdict`.

Topics, for base topic `B`, discovery prefix `P`, and provider key `<provider>`:

| Purpose | Topic | Retain |
|---|---|---|
| Discovery | `P/sensor/pierpressure_<pier>/<provider>_health/config` | yes |
| State | `B/<pier>/health/<provider>/state` | yes |
| Attributes | `B/<pier>/health/<provider>/attributes` | yes |

The provider keys are `open_meteo` and `seven_timer`. The display names are
"Open-Meteo health" and "7Timer! health". The unique identity is
`pierpressure_<pier>_<provider>_health`.

The discovery payload adds `device_class: timestamp` and
`entity_category: diagnostic`. Availability is the shared last-will topic only, with
no template. A failing provider keeps showing its last success.

The state is the last-success time in ISO 8601 with its UTC offset. With no success
yet, the state is the literal `None`. Home Assistant's MQTT sensor reads `None` as
unknown. Publishing it actively replaces any retained time from before a restart.

The attributes payload is:

```json
{
  "provider": "Open-Meteo",
  "role": "base",
  "tracking_since": "2026-10-05T09:00:00+00:00",
  "status": "failed",
  "last_fetch": "2026-10-05T18:00:00+00:00",
  "last_error": "ConnectError",
  "issued_at": "2026-10-05T12:00:00+00:00"
}
```

Before any fetch, `status`, `last_fetch`, `last_error`, and `issued_at` are null.

An `issued_at` can also be null after a success, when the provider gave no issue
time.

`SENSOR_SCHEMA` in `ha_schema.py` gains `device_class` and `entity_category`
(limited to `diagnostic` and `config`). The schema test then checks the new payloads.

- **Alternative considered:** add a `health=` argument to `publish_verdict`, as the
  narrative did. But the verdict publish is already long, and health has its own
  lifecycle. A separate method keeps the verdict path unchanged and testable alone.

### D6 — Errors are built from an allowlist

`describe_error(exc)` builds the error from an allowlist. It never copies the
exception's own text.

- For an HTTP status error, it returns the error type, the status code, and that
  code's standard phrase, such as `HTTPStatusError: 503 Service Unavailable`. The
  phrase comes from Python's `http.HTTPStatus` table. The reason phrase in the
  server's response is never used, because the server controls that text. An
  unknown code gets no phrase.
- For every other error, it returns the error type alone, such as `ConnectError`,
  `ReadTimeout`, or `JSONDecodeError`.

Exception and response text is free-form. httpx puts the full request URL in some messages, and
that URL carries the pier's latitude and longitude. A parser error could quote a
coordinate with no URL around it. Removing URLs would not catch that case, so the
design keeps no free-form text at all. The full message still goes to the log, as
it does today. The error type is enough to tell a network failure from a timeout, an
HTTP error, or a parse failure.

- **Alternative considered:** keep the exception text and remove URLs and numbers.
  A pattern that removes every coordinate also removes useful numbers, and a missed
  format leaks location into Home Assistant's history database. An allowlist cannot
  leak.

### D7 — The README automation alerts on stale or unknown, not unavailable

One template decides whether a provider is failing. It is true when the last success
is older than a chosen number of hours. It is also true when the sensor is `unknown`
and its `tracking_since` attribute is that old. It is false for `unavailable`, which
means the whole process is down and deserves its own alert.

`tracking_since` comes from PierPressure, not from Home Assistant. So a Home
Assistant restart does not reset the count. An entity's `last_changed` time would
reset, which is why the template does not use it.

The automation uses that template twice:

- as a template trigger, which fires when the value turns true while Home Assistant
  runs. Home Assistant re-evaluates a template that uses `now()` every minute.
- as the condition on a Home Assistant start trigger. A template trigger fires only
  on a change from false to true, so a provider already failing at start would never
  fire it. The start trigger covers that case.

A `state` trigger with `for:` was rejected. Home Assistant cancels a pending `for:`
timer on restart, so an already-unknown sensor could stay silent.

The README shows Open-Meteo and says to copy the automation for 7Timer!. It says to
set the threshold to several recompute intervals. It notes that Open-Meteo's issue
time and last success come from the same fetch, so they match closely. The "Removing
the entities" loop gains both health discovery topics.

## Risks / Trade-offs

- [The repository's discovery schemas are hand-authored, so passing them cannot
  prove how Home Assistant behaves] → Verification adds a manual check on a real
  instance (see below).
- [Startup now publishes `online` after the health reset, not inside `connect()`]
  → The delay is a few broker messages. Tests that expect `online` from `connect()`
  move to `go_online()`.
- [Each pier fetches separately, so a flaky network may fail one pier and not
  another] → That is accurate. Health is per pier for that reason.
- [Two more retained entities per pier add MQTT traffic on every publish] → It is
  six small messages per pier per publish, beside a dozen today. No mitigation is
  needed.
- [Health is lost on restart, so a provider failing since before the restart looks
  "unknown" rather than "failing for 3 days"] → Accepted in the story. The
  automation treats a long `unknown` as a failure.
- [Changing `ConditionsProvider`'s return type touches every test stub] → The change
  is mechanical. A helper that wraps bare `Conditions` keeps the stubs short.

## Manual check in Home Assistant

During verification, run the change against a real Home Assistant instance and
confirm these four things:

1. Each health sensor appears under the pier's device as a diagnostic entity.
2. Its state shows as a timestamp after a success.
3. Its state shows as unknown after a restart where the first fetch fails.
4. It stays available while its provider fails.

Current Home Assistant MQTT sensor code reads a `None` payload as unknown. If check
3 fails, change the discovery to a `value_template` that maps the payload to `None`.

## Migration Plan

No migration is needed. On upgrade, the two health sensors per pier appear on the
first publish. To roll back, deploy the earlier image and clear the health discovery
topics, as the README describes.
