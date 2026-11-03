## Why

No provider today brings smoke and haze, which is half of what makes a night
transparent. Open-Meteo's free air-quality endpoint gives aerosol optical depth
and PM2.5 for every hour, and computed transparency (#153) needs them as inputs
before it can be built. This change brings the raw variables in. Nothing judges
them yet.

## What Changes

- **New provider `open_meteo_air_quality`** (display name `Open-Meteo air
  quality`, no key). It declares two new variables, `aerosol_optical_depth` and
  `pm2_5`, and no bundle (D1). It is listed, filled, fetched and reported like
  any other provider, with its own health record (D6).
- **The default provider list gains it**, after `seven_timer`: the default
  becomes `[open_meteo, seven_timer, open_meteo_air_quality]` (D2). A pier with
  its own list is unaffected.
- **Two hidden variables.** The conditions snapshot carries `aerosol_optical_depth`
  and `pm2_5` as reported. The timeline does not show them: a timeline entry
  gains no key, and two snapshots that differ only in these variables yield
  byte-identical verdict documents (D5).
- **The timeline's hours come only from variables it shows** (D3). A variable
  the timeline does not show never adds an entry. The glossary's Timeline entry
  already says so (D4).
- **A provider declares variables by their variable keys**, not their timeline
  keys, in the conditions spec and in the health sensor's `variables` attribute.
  The attribute's values for existing providers do not change.
- **README** documents the provider, its variables, and that nothing reads them
  yet.

Not in this change: dust and other pollutants, any transparency index, and any
change to a gate, the score, a reason or the confidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: a new requirement for the `open_meteo_air_quality` provider and
  its two variables; the default provider list gains it; declarations name
  variables by variable key; the NWS requirement's default-order scenario
  reflects the new default.
- `night-verdict`: the timeline's hours come only from series of variables the
  timeline shows, and hidden variables never change the document.
- `ha-delivery`: provider health's `variables` attribute lists variable keys,
  which need not be timeline keys.

## Impact

- **Code:** a new fetcher in `pierpressure/conditions/` against
  `https://air-quality-api.open-meteo.com/v1/air-quality`, registered in
  `build_provider`; a new spec in `pierpressure/core/providers.py` (`CATALOG`);
  two new members of `Variable` and fields on `SourceReading`; the default list
  in `pierpressure/core/config.py`; the timeline's variable set and hours in
  `pierpressure/core/producer.py` and `pierpressure/core/conditions.py`.
  `TimelineEntry` does not change.
- **Tests and fixtures:** a recorded air-quality fixture; tests that pin the
  default list, the catalog and the timeline.
- **Systems:** default installs make one more keyless request to Open-Meteo per
  recompute, and Home Assistant shows one more provider-health entity.
- **Dependencies:** none.
