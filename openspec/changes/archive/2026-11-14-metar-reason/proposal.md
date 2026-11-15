## Why

Every input to the verdict today is a forecast. At dusk, a forecast of clear
sky can already be wrong, and nothing in the verdict says so. A METAR is a free,
worldwide, hourly observation of the cloud over an airport. Showing the one a
pier names is the first step to a verdict that knows what the sky is doing, and
`metar-confidence` builds on it.

## What Changes

- A pier MAY name an airport weather station with an optional `metar_station`
  (D2). It is not a tuning knob (D3). Add-on users set it in `config.yaml`, as
  they set `dew_margin` (D4).
- For each pier that names a station, every recompute fetches the station's
  latest METAR from the aviationweather.gov Data API, with the same fixed
  User-Agent NWS uses. METAR is not a provider in the provider order and fills
  no variable (D5).
- The observation reaches the core as plain data beside the conditions, so the
  core stays pure and offline. Its time is when the station measured it (D6).
- An observation from more than 90 minutes before the evaluation instant, or
  from after it, is ignored (D7).
- The verdict document gains an additive top-level `observation` object: the
  station, the observation time, the report's overall cover and its cloud
  layers. It is null when there is no usable observation (D8).
- The verdict gains one reason line that says what the station reported and
  when, such as `At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft
  and broken cloud at 4,200 ft.` (D9). A report with no layers says "no cloud
  below 12,000 ft", or "below 5,000 ft" for CAVOK (D10). The line appears on
  every verdict with a usable observation, after the verdict's own terms (D11).
- A `METAR health` sensor shows each fetch for a pier that names a station. A
  failed fetch never fails the verdict (D13, D14).
- The gates, the score and confidence do not change (D12).

No change is **BREAKING**: the delivery surface and every existing field keep
their meaning.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: new requirements for fetching, parsing and timing a METAR
  observation, and for keeping it out of the provider order and the fill.
- `night-verdict`: the pier gains `metar_station` and its validation; the
  document gains `observation`; new requirements for the staleness rule and the
  reason line.
- `ha-delivery`: the health requirements cover a `METAR health` sensor for each
  pier that names a station.

## Impact

- **Code:** a new `pierpressure/conditions/metar.py` (fetch and parse);
  `pierpressure/core/config.py` (`PierConfig`); a plain observation value in the
  core, beside `pierpressure/core/conditions.py`; `pierpressure/core/model.py`
  (`VerdictDocument`); `pierpressure/core/producer.py` (the field and the reason
  line); `pierpressure/service.py` and `pierpressure/health.py` (the fetch and
  its health); the delivery code that publishes health discovery.
- **Tests:** a recorded METAR fixture; config, parser, producer, health and
  service tests; the golden documents under `tests/fixtures/golden/expected/`,
  which gain `observation: null`. The offline guard still holds: the core makes
  no request.
- **Docs:** the README's configuration and verdict-document sections, and
  `ha-addon/DOCS.md` for `metar_station` in `config.yaml`.
- **External:** aviationweather.gov's Data API, with no key, well within its
  100 requests a minute.
- **Card and narrative:** none. Both read `reasons`, so the new line reaches
  them as it is (D15).
- **Glossary:** observation is now in `openspec/glossary.md` (D1).
