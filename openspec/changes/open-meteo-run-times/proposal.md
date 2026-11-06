## Why

The Open-Meteo model providers stamp the fetch time as their issue time, because
the forecast response gives no run time. When RDPS, ICON or GFS fills cloud, a
run 6 to 12 hours old therefore scores as just issued, and confidence overstates
how fresh the forecast is. #154 shipped that gap documented; this change closes
it before agreement (#158) starts comparing model runs.

## What Changes

- Each model provider (`open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`,
  `open_meteo_icon`, `open_meteo_gfs`) reads its model's latest run start from
  Open-Meteo's metadata endpoint, and carries it as the issue time of every
  series it fills (D1).
- Each provider reads one fixed metadata name: HRRR, HRDPS, RDPS, ICON global
  and GFS 0.11° (D2–D6).
- When the metadata call fails, or gives no usable run time, the issue time is
  null and the fetch still succeeds. Freshness then treats the cloud as
  maximally stale, as it already does for a missing issue time (D7–D9).
- The fetch outcome and the health sensor's `issued_at` carry the run time, or
  null, with no new field (D8).
- Plain `open_meteo` and the air-quality provider keep the fetch time (D11).
- The README's model notes, its air-quality note and "Watching provider
  health" say the model providers report their run time, and that only plain
  `open_meteo` and air quality stamp the fetch time.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: the requirement "A model provider's issue time is its fetch
  time" is replaced by one that makes the issue time the model's latest run,
  read from Open-Meteo's metadata, with null when that read fails.

## Impact

- **Code:** `pierpressure/conditions/open_meteo.py` (the model table and
  `OpenMeteoProvider.fetch`), and `pierpressure/conditions/provider.py`
  (`build_provider`, whose docstring says `now` stamps Open-Meteo's issue
  time; that stays true only for plain `open_meteo` and air quality).
  The core is unchanged: `freshness_factor` already reads the cloud series'
  issue time and treats null as stale.
- **Network:** one extra request per model provider per recompute, to
  `https://api.open-meteo.com/data/<name>/static/meta.json`. Keyless, like the
  forecast endpoint.
- **Verdict document and delivery:** no shape change. Confidence for a pier whose
  cloud comes from a model provider drops to reflect the run's real age.
- **Docs:** README model notes, air-quality note and "Watching provider
  health".
- **Dependencies:** none.
