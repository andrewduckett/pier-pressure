## Why

A fire a few tens of kilometres from a pier can spoil transparency before any
smoke forecast shows it. The CAMS smoke forecast works on a 45 km grid and can
miss a fire that close. NASA FIRMS reports satellite fire detections within
about three hours of a pass, free with a MAP_KEY. Naming the nearest one in the
reasons tells the user why tonight's sky may be worse than the forecast says.

## What Changes

- A new, optional top-level `firms` block holds a NASA FIRMS `map_key` for the
  whole service (D2). The key is kept secret: no log line, health error or
  config error ever shows it, or the request URL that contains it (D3). It
  supports `${VAR}`. Add-on users set it in `config.yaml` (D4).
- When the key is set, every fetch for every pier makes one FIRMS area request
  for VIIRS NOAA-20 near-real-time detections from the last day, for a box
  around the pier (D5).
- The detections reach the core as plain data beside the conditions and the
  observation. A fire detection is not an observation and not a provider, and
  fills no variable (D1).
- The core counts only detections with nominal or high confidence, from the 24
  hours up to the evaluation instant, within 50 km of the pier (D6, D7).
- The verdict gains one reason line naming the nearest counted detection: its
  distance, its bearing on an 8-point compass, when it was detected, and how
  many detections are within 50 km (D8). The line appears on every verdict,
  after the observation lines (D9). With no key, a failed fetch or no counted
  detection, there is no line.
- A `FIRMS` health sensor shows each fetch for each pier while the key is set. A
  fetch that finds nothing is a success. A rejected key is a failure (D11).
- The gates, score, confidence, timeline and verdict document keys do not
  change (D10).

No change is **BREAKING**: the delivery surface and every existing field keep
their meaning.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: new requirements for the `firms` block and its key, for
  fetching and parsing FIRMS fire detections, for keeping the key secret, and
  for keeping detections out of the provider order and the fill.
- `night-verdict`: new requirements for which detections count, and for the
  fire reason line and its place.
- `ha-delivery`: the health requirements cover a `FIRMS` health sensor for each
  pier while the key is set.

## Impact

- **Code:** a new `pierpressure/conditions/firms.py` (fetch and parse); a plain
  fire detection value and its reason in the core; `pierpressure/core/config.py`
  (`AppConfig` and a new `FirmsConfig`); `pierpressure/core/producer.py` (the
  reason line); `pierpressure/conditions/provider.py` and
  `pierpressure/service.py` (the fetch beside the providers, and its health).
- **Tests:** a recorded FIRMS fixture trimmed from FIRMS's public, no-key VIIRS
  file (D12); config, parser, producer, health and service tests; a test that
  the key never reaches a log, health error or config error. The golden
  documents do not change, because no golden pier sets a key.
- **Docs:** the README's configuration section and `ha-addon/DOCS.md`.
- **External:** the NASA FIRMS area API, with the user's own MAP_KEY: one
  transaction per pier per fetch, against a limit of 5,000 every 10 minutes.
- **Card and narrative:** none. Both read `reasons`, so the new line reaches
  them as it is.
- **Glossary:** "fire detection" is now in `openspec/glossary.md` (D1).
