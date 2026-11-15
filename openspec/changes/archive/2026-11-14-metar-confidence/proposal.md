## Why

Since `metar-reason`, the verdict quotes what the pier's airport reports, but
confidence still trusts the forecast as if nothing contradicted it. A forecast
that calls the sky clear while the airport reports broken cloud is already
wrong, and the verdict should say how far to trust it for the rest of the
night.

## What Changes

- Confidence gains an observation factor. It runs when the pier has a usable
  observation and the filled cloud series gives low and mid cloud for the clock
  hour that holds the evaluation instant (D2, D3, D6).
- The factor compares the cloud the report proves below 12,000 ft with the
  forecast's low and mid cloud for that hour, never with high cloud (D5, D6).
- It only lowers confidence, and only when the report shows more cloud than the
  forecast. A clear or CAVOK report, or one with less cloud, changes nothing
  (D4). The gap sets the factor with the agreement's bands and factors (D7).
- It multiplies with the agreement factor. Together they never take a MEDIUM
  or HIGH confidence below MEDIUM (D8). It applies on every verdict whose
  confidence comes from the forecast, gated NO-GO included (D9).
- When it lowers confidence, the reasons gain one line, straight after the
  observation line, ending `Confidence lowered.` (D10, D11).
- The gates and the score do not change. The verdict document gains no field
  (D12). The card and the narrative need no change (D13).

No change is **BREAKING**: the delivery surface and every existing field keep
their meaning. Confidence values change only for piers that name a station.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: the confidence requirements gain the observation factor and
  its reason line; "the observation changes no gate, score or confidence" now
  allows confidence to fall; the observation line is no longer always the
  core's last line (D14).

## Impact

- **Code:** `pierpressure/core/scoring.py` (`confidence`, `evaluate` and the new
  factor and reason line); `pierpressure/core/observation.py` (the cloud a report
  proves); `pierpressure/core/producer.py` (passes the usable observation to the
  decision, and places the new line).
- **Tests:** scoring and producer tests at the edges: a stale report, a hour
  with no low or mid value, a clear report, a CAVOK report, and agreement and
  the observation together. Golden documents keep `observation: null`, so they
  do not change.
- **Docs:** the README's `metar_station` row, which says the observation never
  changes confidence, and its `confidence` field row.
- **Card, narrative and delivery:** none (D13).
- **Glossary:** none (D1).
