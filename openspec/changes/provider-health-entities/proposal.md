## Why

Issue #25. Today a failing weather provider shows only in the logs. The verdict shows
that conditions are missing, but not which provider failed, why, or for how long.
Losing 7Timer! only lowers confidence, so a broken 7Timer! is easy to miss for days.
Once other people run the published image, a broken provider affects all of them. A
sensor per provider lets the maintainer see the problem in Home Assistant and notify
on it, the same way verdict notifications already work.

## What Changes

- Add one diagnostic sensor per pier for each conditions provider: "Open-Meteo
  health" and "7Timer! health". Each sensor is named after its provider.
- The sensor's state is the time of the provider's last successful fetch for that
  pier. Its attributes give the provider's role (`base` or `secondary`), the status
  of the latest fetch (`ok` or `failed`), when that fetch ran, the last error, and the
  issue time of the data from the last successful fetch.
- A fetch that returns no readings counts as `failed`, with its own error text. This
  matches the conditions rule that an empty fetch leaves the source unavailable. A
  fetch that returns readings with some blank fields counts as `ok`.
- Health is kept in memory only. On startup, the system clears each sensor before it
  fetches anything. The last success then stays unknown until the provider next
  succeeds.
- Health travels beside the verdict document, not inside it. The verdict, score, and
  confidence never read it. The verdict document does not change.
- The health sensors are available whenever the process is online. A failing provider
  keeps showing its last success time, because the age of that time is the signal.
- The error shows only the error type, plus the status code and reason for an HTTP
  error. It never copies the error's own text, which can hold the request URL and
  the pier's coordinates. The full text still goes to the log.
- The README gains an example automation. It notifies when a provider has not
  succeeded for a chosen number of hours, including after a restart, when the last
  success is unknown. The README's "Removing the entities" steps gain the two new
  discovery topics.

This change is additive. Every existing entity, topic, and mapping stays the same.

Out of scope:

- Retrying a failed fetch (#38). The health sensors will show how often one-off
  failures happen.
- Health for the LLM explainer provider.
- Keeping health across restarts.
- Changing fallback behaviour.
- A scheduled CI check against the real provider APIs (Won't, see epic #19).
- Renaming `CompositeProvider`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: add a requirement that each fetch reports its outcome per provider,
  with an empty fetch reported as failed, and that this outcome never reaches the
  verdict.
- `ha-delivery`: add a requirement that exposes provider health as diagnostic
  entities, one per pier per provider.

## Impact

- **Code:** a new `pierpressure/health.py` holds provider-neutral health types and
  the rule that folds each fetch into a provider's health.
  `pierpressure/conditions/provider.py` reports each fetch's outcome.
  `pierpressure/service.py` keeps health per pier and publishes it.
  `pierpressure/delivery/mqtt.py` gains the health discovery and state.
  `pierpressure/delivery/ha_schema.py` accepts `device_class` and `entity_category`.
- **Core:** `pierpressure/core/` does not change. Every golden verdict stays
  byte-identical.
- **Tests:** new tests for the health rule, the provider outcomes, the service wiring,
  and the delivery payloads.
- **Docs:** `README.md`. A new decision record may follow from the ADR review.
- **Users:** two new diagnostic entities per pier appear in Home Assistant. Nothing
  else changes.
- **Dependencies:** none.
