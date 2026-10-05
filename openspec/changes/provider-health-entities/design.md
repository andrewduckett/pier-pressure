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
which shortens an exception for display (see D5).

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

The first thing `Service.run()` does is publish that seeded health for every pier.
It does this before any fetch or narrative call, so the startup publish waits on
nothing but the broker. This replaces any retained health from before the restart.
Without it, a slow first fetch would leave an old success time showing as current
while the process is online. If the publish fails, `DeliveryError` ends the process
as it does today, and the last-will message marks it offline.

A sub-second window remains between the `online` message in `connect()` and this
first publish. Only broker messages fall inside it, so Home Assistant could at most
flash the old value. Moving the `online` message later would change the existing
startup contract for every entity, which costs more than the flash.

`CompositeProvider` exposes its providers (key, display name, role) so `__main__.py`
can pass them to the service. The default no-conditions provider has none, so a
service built without one publishes no health.

The fetch time comes from a `now` function injected into `CompositeProvider`.
`__main__.py` passes the service's `SystemClock`. Tests pass a fixed clock, so every
payload is deterministic.

Health is never written to disk. After a restart, every provider starts with no
history.

### D4 — A separate `publish_health` method in delivery

`MqttDelivery.publish_health(pier_id, healths)` publishes discovery, state, and
attributes for each health record. `publish_verdict` does not change. The service
calls `publish_health` right after `publish_verdict`.

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
  "status": "failed",
  "last_fetch": "2026-10-05T18:00:00+00:00",
  "last_error": "ConnectError",
  "issued_at": "2026-10-05T12:00:00+00:00"
}
```

Before any fetch, `status`, `last_fetch`, `last_error`, and `issued_at` are null.

`SENSOR_SCHEMA` in `ha_schema.py` gains `device_class` and `entity_category`
(limited to `diagnostic` and `config`). The schema test then checks the new payloads.

- **Alternative considered:** add a `health=` argument to `publish_verdict`, as the
  narrative did. But the verdict publish is already long, and health has its own
  lifecycle. A separate method keeps the verdict path unchanged and testable alone.

### D5 — Errors are shortened before they leave the provider layer

`describe_error(exc)` builds the error from an allowlist. It never copies the
exception's own text.

- For an HTTP status error, it returns the error type, status code, and reason, such
  as `HTTPStatusError: 503 Service Unavailable`.
- For every other error, it returns the error type alone, such as `ConnectError`,
  `ReadTimeout`, or `JSONDecodeError`.

Exception text is free-form. httpx puts the full request URL in some messages, and
that URL carries the pier's latitude and longitude. A parser error could quote a
coordinate with no URL around it. Removing URLs would not catch that case, so the
design keeps no free-form text at all. The full message still goes to the log, as
it does today. The error type is enough to tell a network failure from a timeout, an
HTTP error, or a parse failure.

- **Alternative considered:** keep the exception text and remove URLs and numbers.
  A pattern that removes every coordinate also removes useful numbers, and a missed
  format leaks location into Home Assistant's history database. An allowlist cannot
  leak.

### D6 — The README automation alerts on stale or unknown, not unavailable

One template decides whether a provider is failing. It is true when the last success
is older than a chosen number of hours. It is also true when the sensor has been
`unknown` for that long, judged by the entity's `last_changed` time. It is false for
`unavailable`, which means the whole process is down and deserves its own alert.

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
time and last success come from the same fetch, so they match closely. The "Removing the entities" loop gains both
health discovery topics.

## Risks / Trade-offs

- [The repository's discovery schemas are hand-authored, so passing them cannot
  prove Home Assistant's behaviour] → Verification includes a manual check on a real
  instance: the sensor shows as a diagnostic timestamp, the `None` state shows as
  unknown, and the sensor stays available while its provider fails. Current Home
  Assistant MQTT sensor code reads `None` as unknown. If that check fails, switch to
  a `value_template` that maps the payload to `None`.
- [After a Home Assistant restart, `last_changed` resets, so an `unknown` sensor
  alerts only after the threshold passes again] → Accepted. The start trigger still
  alerts at once on a stale success time.
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

## Migration Plan

No migration is needed. On upgrade, the two health sensors per pier appear on the
first publish. To roll back, deploy the earlier image and clear the health discovery
topics, as the README describes.
