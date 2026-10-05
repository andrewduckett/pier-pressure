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
  therefore always equals its last-success time.
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
`FetchAttempt` per provider it tried. A `FetchAttempt` holds the provider's key,
display name, role, the fetch time, whether it succeeded, the error, and the issue
time.

`_safe_fetch` builds the attempt. An exception gives a failed attempt. An empty
forecast also gives a failed attempt, with the error `no readings returned`. A
forecast with readings gives a successful attempt, whatever its blank fields.

The service unpacks the result. It passes only `conditions` to `produce_verdict`. So
"health never reaches the verdict" holds by structure, not by care.

- **Alternative considered:** inject a mutable health tracker into
  `CompositeProvider` and have the service read it after each fetch. It changes
  fewer signatures. But the data then flows by a side channel, and tests must set up
  shared state to see it. An explicit return value is easier to follow and test.

### D2 — Provider-neutral health types live in `pierpressure/health.py`

The new module holds `FetchAttempt`, `ProviderHealth`, and a pure function
`fold(previous, attempt) -> ProviderHealth`. It also holds `describe_error(exc)`,
which shortens an exception for display (see D5).

`fold` applies these rules:

- A successful attempt sets `last_success` to the attempt time and `issued_at` to
  the attempt's issue time.
- A failed attempt keeps the earlier `last_success` and `issued_at`.
- Every attempt replaces the latest status, the latest attempt time, and the error.
  A success clears the error.

The module sits outside `pierpressure/core/`. Health describes the edge of the
system, and the core-boundary test keeps it that way. It also sits outside
`pierpressure/conditions/`, so nothing in it assumes weather.

- **Alternative considered:** `pierpressure/conditions/health.py`. It is closer to
  its only caller today. But it would have to move if the explainer ever reports
  health, and moving it later costs more than placing it well now.

### D3 — The service holds health in memory, per pier and provider

The service keeps a dictionary keyed by pier and provider key. On each publish it
folds that fetch's attempts into the dictionary, then publishes the pier's health.

The service seeds the dictionary at startup with every configured provider, each
with no history. So discovery covers every configured provider, even one not tried
on a given publish. With today's composite, both providers are tried on every
fetch. The seeding matters only for a future failover chain.

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
  "last_attempt": "2026-10-05T18:00:00+00:00",
  "last_error": "ConnectError: [Errno -3] Temporary failure in name resolution",
  "issued_at": "2026-10-05T12:00:00+00:00"
}
```

Before any fetch, `status` and `last_attempt` are null.

`SENSOR_SCHEMA` in `ha_schema.py` gains `device_class` and `entity_category`
(limited to `diagnostic` and `config`). The schema test then checks the new payloads.

- **Alternative considered:** add a `health=` argument to `publish_verdict`, as the
  narrative did. But the verdict publish is already long, and health has its own
  lifecycle. A separate method keeps the verdict path unchanged and testable alone.

### D5 — Errors are shortened before they leave the provider layer

`describe_error(exc)` returns `<ExceptionType>: <message>`. For an HTTP status error
the message is the status code and reason, such as `HTTPStatusError: 503 Service
Unavailable`. For other errors it uses the exception's own text, with every URL
removed and the result cut to 200 characters.

httpx puts the full request URL in some messages. That URL carries the pier's
latitude and longitude. Stripping URLs keeps coordinates out of Home Assistant's
attributes and its history database.

### D6 — The README automation alerts on stale or unknown, not unavailable

The README example uses two triggers. A template trigger fires when the last success
is older than a chosen number of hours. A state trigger fires when the sensor has
been `unknown` for that long. Neither fires on `unavailable`, which means the whole
process is down and deserves its own alert.

The README shows Open-Meteo and says to copy the automation for 7Timer!. It says to
set the threshold to several recompute intervals. It notes that Open-Meteo's issue
time always equals its last success. The "Removing the entities" loop gains both
health discovery topics.

## Risks / Trade-offs

- [Home Assistant might not read the `None` payload as unknown for a timestamp
  sensor] → Check it on a real instance during verification. If it fails, switch to
  a `value_template` that maps an empty payload to `None`.
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
